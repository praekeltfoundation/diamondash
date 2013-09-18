window.diamondash = function() {
  return {
  };
}.call(this);

diamondash.utils = function() {
  function objectByName(name, that) {
    return _(name.split( '.' )).reduce(
      function(obj, propName) { return obj[propName]; },
      that || this);
  }

  function bindEvents(events, that) {
    that = that || this;

    _(events).each(function(fn, e) {
      var parts = e.split(' '),
          event = parts[0],
          entity = parts[1];

      if (entity) { that.listenTo(objectByName(entity, that), event, fn); }
      else { that.on(event, fn); }
    });
  }

  function ColorMaker(options) {
    options = _({}).defaults(options, this.defaults);
    this.colors = options.scale.domain(d3.range(0, options.n));
    this.i = 0;
  }

  ColorMaker.prototype = {
    defaults: {
      scale: d3.scale.category10(),
      n: 10
    },

    next: function() {
      return this.colors(this.i++);
    }
  };

  return {
    objectByName: objectByName,
    bindEvents: bindEvents,
    ColorMaker: ColorMaker
  };
}.call(this);

diamondash.widgets = function() {
  function WidgetRegistry(widgets) {
    this.widgets = {};
    
    _(widgets || {}).each(function(options, name) {
      this.add(name, options);
    }, this);
  };

  WidgetRegistry.prototype = {
    add: function(name, options) {
      if (name in this.widgets) {
        throw new Error("Widget type '" + name + "' already exists.");
      }

      options = options || {};
      this.widgets[name] = {
        view: options.view || diamondash.widgets.widget.WidgetView,
        model: options.model || diamondash.widgets.widget.WidgetModel
      };
    },

    get: function(name) {
      return this.widgets[name];
    },

    remove: function(name) {
      var widget = this.get(name);
      delete this.widgets[name];
      return widget;
    }
  };

  return {
    registry: new WidgetRegistry(),
    WidgetRegistry: WidgetRegistry
  };
}.call(this);

diamondash.widgets.widget = function() {
  var widgets = diamondash.widgets;

  var WidgetModel = Backbone.RelationalModel.extend({
    idAttribute: 'name',
    isStatic: false,

    _fetch: Backbone.Model.prototype.fetch,
    fetch: function() {
      if (!this.isStatic) {
        this._fetch();
      }
    },

    _parse: Backbone.Model.prototype.parse,
    parse: function(response, options) {
      if (response && !_.isEmpty(response)) {
        return this._parse(response, options);
      }
    },

    url: function() {
      return '/api/widgets/'
        + this.get('dashboardName') + '/'
        + this.get('name')
        + '/snapshot';
    }
  });

  var WidgetCollection = Backbone.Collection.extend({
    model: WidgetModel
  });

  var WidgetView = Backbone.View.extend({
  });

  return {
    WidgetModel: WidgetModel,
    WidgetCollection: WidgetCollection,
    WidgetView: WidgetView
  };
}.call(this);

diamondash.widgets.graph = function() {
  var utils = diamondash.utils,
      widgets = diamondash.widgets;

  var GraphMetricModel = Backbone.RelationalModel.extend({
    idAttribute: 'name',

    defaults: {
      'datapoints': [],
    },

    bisect: d3
      .bisector(function(d) { return d.x; })
      .left,

    lastValue: function(x) {
      var datapoints = this.get('datapoints'),
          d = datapoints[datapoints.length - 1];

      return d && typeof d.y !== 'undefined'
        ? d.y
        : null;
    },

    valueAt: function(x) {
      var datapoints = this.get('datapoints'),
          i = this.bisect(datapoints, x);
          d = datapoints[i];

      return d && x === d.x
        ? d.y
        : null;
    }
  });

  var GraphMetricCollection = Backbone.Collection.extend({
    colorOptions: {
      n: 10,
      scale: d3.scale.category10()
    },

    initialize: function() {
      this.colors = new utils.ColorMaker(this.colorOptions);
      utils.bindEvents(this.bindings, this);
    },

    bindings: {
      'add': function(metric) {
        metric.set('color', this.colors.next());
      }
    }
  });

  var GraphModel = widgets.widget.WidgetModel.extend({
    isStatic: false,

    relations: [{
      type: Backbone.HasMany,
      key: 'metrics',
      relatedModel: GraphMetricModel,
      collectionType: GraphMetricCollection
    }],

    defaults: {
      'domain': 0,
      'range': 0,
      'metrics': []
    },
  });

  var GraphLegendView = Backbone.View.extend({
    jst: JST['diamondash/widgets/graph/legend.jst'],

    initialize: function(options) {
      this.graph = options.graph;
      this.model = this.graph.model;
      utils.bindEvents(this.bindings, this);
    },

    format: function() {
      var format = d3.format(",f");

      return function(v) {
        return v !== null
          ? format(v)
          : '';
      };
    }(),

    render: function(x) {
      this.$el.html(this.jst({
        self: this,
        x: x
      }));

      var metrics = this.model.get('metrics');
      this.$('.legend-item').each(function() {
        var $el = $(this),
            name = $el.attr('data-name');

        $el.css('background', metrics.get('color'));
      });

      return this;
    },

    bindings: {
      'hover graph': function() {
        this.$el.addClass('hover');
        return this.render(x);
      },

      'unhover graph': function() {
        this.$el.removeClass('hover');
        return this.render();
      }
    }
  });

  var GraphView = widgets.widget.WidgetView.extend({
    svgHeight: 214,
    axisHeight: 24,
    axisMarkerWidth: 128,
    markerCollisionDistance: 60,
    hoverDotSize: 4,
    dottedHoverDotSize: 5,
    dotSize: 3,
    margin: {top: 4, right: 4, bottom: 0, left: 4},

    formatTime: function() {
      var format = d3.time.format.utc("%d-%m %H:%M");
      return function(t) { return format(new Date(t)); };
    }(),

    initialize: function(options) {
      var self = this,
          metrics = this.model.get('metrics').models,
          d3el = d3.select(this.el);

      // Parse Config
      // ------------
      if (options.config) {
        var config = options.config;

        this.dotted = 'dotted' in config ? config.dotted : false;
        this.smooth = 'smooth' in config ? config.smooth : true;
      }

      // Dimensions Setup
      // -------------
      var margin = this.margin;
      this.width = this.$el.width();
      this.chartWidth = this.width - margin.left - margin.right;
      this.chartHeight = this.svgHeight
            - this.axisHeight - margin.top - margin.bottom;
      this.axisVPosition = this.svgHeight - this.axisHeight;

      // Chart Setup
      // -----------
      var svg = this.svg = d3el.append('svg')
          .attr('class', 'graph-svg')
          .attr('width', this.width)
          .attr('height', this.svgHeight)
        .append('g')
          .attr('transform', "translate(" + margin.left + "," + margin.top + ")");

      var fx, fy;
      this.fx = fx = d3.time.scale().range([0, this.chartWidth]);
      this.fy = fy = d3.scale.linear().range([this.chartHeight, 0]);

      this.maxTicks = Math.floor(this.chartWidth / this.axisMarkerWidth);
      this.axis = d3.svg.axis()
        .scale(fx)
        .orient('bottom')
        .tickFormat(this.formatTime)
        .ticks(this.maxTicks);

      this.line = d3.svg.line()
        .interpolate(this.smooth ? 'monotone' : 'linear')
        .x(function(d) { return fx(d.x); })
        .y(function(d) { return fy(d.y); });

      var chart = this.chart = svg.append('g')
        .attr('class', 'chart')
        .attr('height', this.chartHeight);

      this.axisLine = svg.append("g")
        .attr('class', 'axis')
        .attr('transform', "translate(0, " + this.axisVPosition + ")")
        .call(this.axis);

      // Legend Setup
      // -----------
      this.legend = new GraphLegendView({graph: this});

      // Hover Setup
      // -----------
      
      // create an overlay to catch events
      this.svg.append('rect')
        .attr('class', 'event-overlay')
        .attr('fill-opacity', 0)
        .attr('width', this.width)
        .attr('height', this.svgHeight)
        .on('mousemove',
            function() { self.focus.call(self, d3.mouse(this)[0]); })
        .on('mouseout',
            function() { self.unfocus.call(self); });

      // Model-View Bindings Setup
      // -------------------------
      this.model.on('change', this.render, this);
    },

    snapX: function(x) {
      var start = this.model.get('domain')[0] || 0,
          step = this.model.get('step'),
          i = Math.round((x - start) / step);

      return start + (step * i);
    },

    buildHoverMarker: function(g) {
      // Replicates the way d3 generates axis time markers.
      // (cloning of one of one of the axis time markers could be done instead,
      // but that is not d3-like).

      g.attr('class', 'hover-marker');

      g.append('line')
        .attr('class', 'tick')
        .attr('y2', 6)
        .attr('x2', 0);

      g.append('text')
        .attr('text-anchor', "middle")
        .attr('dy', ".71em")
        .attr('y', 9)
        .attr('x', 0)
        .attr('fill-opacity', 0);

      return g;
    },

    focus: function(svgX) {
      var fx = this.fx,
          fy = this.fy;
    
      // convert the svg x value to the corresponding time x value, then snap it
      // to the closest timestep
      var x = this.snapX(fx.invert(svgX));
      svgX = fx(x);

      var metrics = this.model.get('metrics');
      var metricValues = metrics.invoke('valueAt', x);

      // draw hover marker
      var hoverMarker = this.axisLine.selectAll('.hover-marker').data([null]);
      hoverMarker.enter().append('g')
        .call(this.buildHoverMarker)
        .transition().select('text').attr('fill-opacity', 1);
      hoverMarker
        .attr('transform', "translate(" + svgX + ", 0)")
        .select('text').text(this.formatTime(x));

      // hide axis markers colliding with hover marker
      var markerCollisionDistance = this.markerCollisionDistance;
      this.axisLine.selectAll('g')
        .style('fill-opacity', function(d) {
          return Math.abs(fx(d) - svgX) < markerCollisionDistance ? 0 : 1;
        });

      // draw dots
      var dots = this.svg.selectAll('.hover-dot')
        .data(_.reject(metricValues, function(d) { return d === null; }));

      dots.enter().append('circle')
        .attr('class', 'hover-dot')
        .style('stroke', function(d, i) { return metrics.at(i).get('color'); })
        .transition()
          .attr('r', this.dotted ? this.dottedHoverDotSize : this.hoverDotSize);

      dots.attr('cx', svgX)
          .attr('cy', fy);

      return this;
    },

    unfocus: function() {
      this.svg.selectAll('.hover-dot, .hover-marker').remove();
      this.axisLine.selectAll('g').style('fill-opacity', 1);
    }, 

    genTickValues: function(start, end, step) {
      var n = (end - start) / step,
          m = this.maxTicks,
          i = 1;

      while (Math.floor(n / i) > m) i++;
      return d3.range(start, end, step * i);
    },

    render: function() {
      var model = this.model,
          line = this.line,
          metrics = model.get('metrics').models,
          domain = model.get('domain'),
          range = model.get('range'),
          step = model.get('step'),
          fx = this.fx,
          fy = this.fy;

      fx.domain(domain);
      fy.domain(range);

      this.axis.tickValues(this.genTickValues.apply(this, domain.concat([step])));
      this.axisLine.call(this.axis);

      var lines = this.chart.selectAll('.line').data(metrics);
      lines.enter().append('path')
        .attr('class', 'line')
        .style('stroke', function(d) { return d.get('color'); });
      lines.attr('d', function(d) { return line(d.get('datapoints')); });

      if (this.dotted) {
        var dotGroups = this.chart.selectAll('.dot-group').data(metrics);
        dotGroups.enter().append('g')
          .attr('class', 'dot-group')
          .style('fill', function(d) { return d.get('color'); });
        dotGroups.exit().remove();

        var dots = dotGroups.selectAll('.dot')
          .data(function(d) { return d.get('datapoints'); });
        dots.enter().append('circle')
          .attr('class', 'dot')
          .attr('r', this.dotSize);
        dots.exit().remove();
        dots
          .attr('cx', function(d) { return fx(d.x); })
          .attr('cy', function(d) { return fy(d.y); });
      }

      this.legend.render();
    }
  });

  widgets.registry.add('graph', {
    model: GraphModel,
    view: GraphView
  });

  return {
    GraphModel: GraphModel,
    GraphMetricModel: GraphMetricModel,
    GraphMetricCollection: GraphMetricCollection,
    GraphView: GraphView
  };
}.call(this);

diamondash.widgets.lvalue = function() {
  var widgets = diamondash.widgets;

  var LValueModel = widgets.widget.WidgetModel.extend({
    isStatic: false
  });

  var LastValueView = Backbone.View.extend({
    fadeDuration: 200,

    initialize: function(options) {
      this.widget = options.widget;
    },

    format: {
      short: d3.format(".2s"),
      long: d3.format(",f")
    },

    blink: function(fn) {
      var self = this;

      this.$el.fadeOut(this.fadeDuration, function() {
        fn.call(self);
        self.$el.fadeIn(self.fadeDuration);
      });
    },

    render: function(longMode) {
      this.blink(function() {
        if (longMode) {
          this.$el
            .addClass('long')
            .removeClass('short')
            .text(this.format.long(this.model.get('last')));
        } else {
          this.$el
            .addClass('short')
            .removeClass('long')
            .text(this.format.short(this.model.get('last')));
        }
      });
    }
  });

  var LValueView = widgets.widget.WidgetView.extend({
    jst: JST['diamondash/widgets/lvalue/lvalue.jst'],
   
    initialize: function(options) {
      this.listenTo(this.model, 'change', this.render);

      this.last = new LastValueView({
        widget: this,
        model: this.model
      });

      this.mouseIsOver = false;
    },

    format: {
      diff: d3.format("+.3s"),
      percentage: d3.format(".2%"),

      _time: d3.time.format.utc("%d-%m-%Y %H:%M"),
      time: function(t) { return this._time(new Date(t)); },
    },

    render: function() {
      var model = this.model,
          last = model.get('last'),
          prev = model.get('prev'),
          diff = last - prev;

      var change;
      if (diff > 0) { change = 'good'; }
      else if (diff < 0) { change = 'bad'; }
      else { change = 'no'; }

      this.$('.widget-container').html(this.jst({
        from: this.format.time(model.get('from')),
        to: this.format.time(model.get('to')),
        diff: this.format.diff(diff),
        change: change,
        percentage: this.format.percentage(diff / (prev || 1))
      }));

      this.last
        .setElement(this.$('.last'))
        .render(this.mouseIsOver);
    },

    events: {
      'mouseenter': function() {
        this.mouseIsOver = true;
        this.last.render(true);
      },

      'mouseleave': function() {
        this.mouseIsOver = false;
        this.last.render(false);
      }
    }
  });

  widgets.registry.add('lvalue', {
    model: LValueModel,
    view: LValueView
  });

  return {
    LValueModel: LValueModel,
    LastValueView: LastValueView,
    LValueView: LValueView 
  };
}.call(this);

diamondash.dashboard = function() {
  WidgetCollection = diamondash.widgets.widget.WidgetCollection;

  function DashboardController(args) {
    this.name = args.name;
    this.widgets = args.widgets;
    this.widgetViews = args.widgetViews;
    this.requestInterval = args.requestInterval;
  }

  DashboardController.DEFAULT_REQUEST_INTERVAL = 10000;

  DashboardController.fromConfig = function(config) {
    var dashboardName = config.name;

    var widgets = new WidgetCollection(),
        widgetViews = [];

    var requestInterval = config.requestInterval
                       || DashboardController.DEFAULT_REQUEST_INTERVAL;

    config.widgets.forEach(function(widgetConfig) {
      var widgetType = diamondash.widgets.registry.get(widgetConfig.typeName);

      var model = new widgetType.model(
        _({dashboardName: dashboardName}).extend(widgetConfig.model),
        {collection: widgets});

      widgets.add(model);

      widgetViews.push(new widgetType.view({
        el: $("#" + model.get('name')),
        model: model,
        config: widgetConfig.view
      }));
    });

    return new DashboardController({
      name: dashboardName,
      widgets: widgets,
      widgetViews: widgetViews,
      requestInterval: requestInterval
    });
  };

  DashboardController.prototype = {
    fetch: function() {
      this.widgets.forEach(function(m) { return m.fetch(); });
    },
    start: function() {
      var self = this;

      self.fetch();
      setInterval(
        function() { self.fetch.call(self); },
        this.requestInterval);
    }
  };

  return {
    DashboardController: DashboardController
  };
}.call(this);
