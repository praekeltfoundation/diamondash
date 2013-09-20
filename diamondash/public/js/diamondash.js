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

  function maybeByName(obj, that) {
    return _.isString(obj)
      ? objectByName(obj, that)
      : obj;
  }

  function functor(obj) {
    return !_.isFunction(obj)
      ? function() { return obj; }
      : obj;
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

  function snap(x, start, step) {
    var i = Math.round((x - start) / step);
    return start + (step * i);
  }

  function d3Map(selection, fn) {
    var values = [];

    selection.each(function(d, i) {
      values.push(fn.call(this, d, i));
    });

    return values;
  }

  return {
    functor: functor,
    objectByName: objectByName,
    maybeByName: maybeByName,
    bindEvents: bindEvents,
    snap: snap,
    d3Map: d3Map
  };
}.call(this);

diamondash.components = function() {
  return {
  };
}.call(this);

diamondash.components.structures = function() {
  function Extendable() {}
  Extendable.extend = Backbone.Model.extend;

  var Eventable = Extendable.extend(Backbone.Events);

  var ColorMaker = Extendable.extend({
    constructor: function(options) {
      options = _({}).defaults(options, this.defaults);
      this.colors = options.scale.domain(d3.range(0, options.n));
      this.i = 0;
    },

    defaults: {
      scale: d3.scale.category10(),
      n: 10
    },

    next: function() {
      return this.colors(this.i++);
    }
  });

  Registry = Eventable.extend({
    constructor: function(items) {
      this.items = {};
      
      _(items || {}).each(function(data, name) {
        this.add(name, data);
      }, this);
    },

    processAdd: function(name, data) {
      return data;
    },

    processGet: function(name, data) {
      return data;
    },

    add: function(name, data) {
      if (name in this.items) {
        throw new Error("'" + name + "' is already registered.");
      }

      data = this.processAdd(name, data);
      this.trigger('add', name, data);
      this.items[name] = data;
    },

    get: function(name) {
      return this.processGet(name, this.items[name]);
    },

    remove: function(name) {
      var data = this.items[name];
      this.trigger('remove', name, data);
      delete this.items[name];
      return data;
    }
  });

  return {
    Extendable: Extendable,
    Eventable: Eventable,
    Registry: Registry,
    ColorMaker: ColorMaker
  };
}.call(this);

diamondash.components.charts = function() {
  var structures = diamondash.components.structures,
      utils = diamondash.utils;

  var components = {};

  components.svg = function(target, dimensions) {
    return target.append('svg')
      .attr('width', dimensions.width)
      .attr('height', dimensions.height)
      .append('g')
        .attr('transform', "translate("
          + dimensions.margin.left
          + ","
          + dimensions.margin.top + ")");
  };

  // Replicates the way d3 generates axis time markers
  components.marker = function(target) {
    target.append('line')
      .attr('class', 'tick')
      .attr('y2', 6)
      .attr('x2', 0);

    target.append('text')
      .attr('text-anchor', "middle")
      .attr('dy', ".71em")
      .attr('y', 9)
      .attr('x', 0)
      .attr('fill-opacity', 0);

    return target;
  };

  var Dimensions = structures.Extendable.extend({
    height: 0,
    width: 0,

    margin: {
      top: 0,
      right: 0,
      bottom: 0,
      left: 0
    },

    constructor: function(options) {
      options = options || {};

      if ('height' in options) { this.height = options.height; }
      if ('width' in options) { this.width = options.width; }

      if (options.margin) {
        this.margin = _({}).defaults(options.margin, this.margin);
      }

      this.innerWidth = this.width - this.margin.left - this.margin.right;
      this.innerHeight = this.height - this.margin.top - this.margin.bottom;
    }
  });

  var AxisView = structures.Eventable.extend({
    height: 24,
    orient: 'bottom',

    // An approximation to estimate a well-fitting tick count
    markerWidth: 128,

    constructor: function(options) {
      this.chart = options.chart;
      this.scale = options.scale;

      if ('format' in options) { this.format = options.format; }
      if ('orient' in options) { this.orient = options.orient; }
      if ('height' in options) { this.height = options.height; }

      if ('tickCount' in options) { this.tickCount = options.tickCount; }
      if ('tickValues' in options) { this.tickValues = options.tickValues; }

      this.axis = d3.svg.axis()
        .scale(this.scale)
        .orient(this.orient)
        .tickFormat(this.format)
        .ticks(_(this).result('tickCount'));

      this.line = this.chart.svg.append("g")
        .attr('class', 'axis')
        .attr('transform', this._translation())
        .call(this.axis);
    },

    _translation: function() {
      var p;

      if (this.orient == 'top') {
        return "translate(0, " + this.height + ")";
      }
      else if (this.orient == 'left') {
        return "translate(" + this.height + ", 0)";
      }
      else if (this.orient == 'right') {
        p = this.chart.dimensions.width - this.height;
        return "translate(" + p + ", 0)";
      }

      p = this.chart.dimensions.height - this.height;
      return "translate(0, " + p + ")";
    },

    format: function() {
      var format = d3.time.format.utc("%d-%m %H:%M");
      return function(t) { return format(new Date(t)); };
    }(),

    tickCount: function() {
      var width = this.chart.dimensions.innerWidth,
          count = Math.floor(width / this.markerWidth);

      return Math.max(0, count);
    },

    tickValues: function(start, end, step) {
      var n = (end - start) / step,
          m = _(this).result('tickCount'),
          i = 1;

      while (Math.floor(n / i) > m) i++;

      var values = d3.range(start, end, step * i);
      values.push(end);

      return values;
    },

    render: function(start, end, step) {
      this.axis.tickValues(this.tickValues(start, end, step));
      this.line.call(this.axis);
      return this;
    }
  });

  var ChartView = Backbone.View.extend({
    className: 'chart',

    initialize: function(options) {
      this.dimensions = options.dimensions;
      this.svg = components.svg(d3.select(this.el), this.dimensions);

      var self = this;
      this.overlay = this.svg.append('rect')
        .attr('class', 'event-overlay')
        .attr('fill-opacity', 0)
        .attr('width', this.dimensions.width)
        .attr('height', this.dimensions.height)
        .on('mousemove', function() {
          self.trigger('mousemove', this);
        })
        .on('mouseout', function() {
          self.trigger('mouseout', this);
        });
    }
  });

  return {
    components: components,
    AxisView: AxisView,
    ChartView: ChartView,
    Dimensions: Dimensions
  };
}.call(this);

diamondash.widgets = function() {
  var structures = diamondash.components.structures,
      utils = diamondash.utils;

  var WidgetRegistry = structures.Registry.extend({
    processAdd: function(name, options) {
      return _({}).defaults(options, {
        view: 'diamondash.widgets.widget.WidgetView',
        model: 'diamondash.widgets.widget.WidgetModel'
      });
    },

    processGet: function(name, options) {
      return {
        view: utils.maybeByName(options.view),
        model: utils.maybeByName(options.model)
      };
    }
  });

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
  diamondash.widgets.registry.add('graph', {
    model: 'diamondash.widgets.graph.models.GraphModel',
    view: 'diamondash.widgets.graph.views.GraphView'
  });

  return {
  };
}.call(this);

diamondash.widgets.graph.models = function() {
  var widget = diamondash.widgets.widget,
      structures = diamondash.components.structures,
      utils = diamondash.utils;

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
      this.colors = new structures.ColorMaker(this.colorOptions);
      utils.bindEvents(this.bindings, this);
    },

    bindings: {
      'add': function(metric) {
        metric.set('color', this.colors.next());
      }
    }
  });

  var GraphModel = widget.WidgetModel.extend({
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

  return {
    GraphModel: GraphModel,
    GraphMetricModel: GraphMetricModel,
    GraphMetricCollection: GraphMetricCollection,
  };
}.call(this);

diamondash.widgets.graph.views = function() {
  var utils = diamondash.utils,
      structures = diamondash.components.structures,
      charts = diamondash.components.charts;

  var GraphLegendView = Backbone.View.extend({
    className: 'legend',

    jst: JST['diamondash/widgets/graph/legend.jst'],

    initialize: function(options) {
      this.graph = options.graph;
      this.model = this.graph.model;
      utils.bindEvents(this.bindings, this);
    },

    format: d3.format(",f"),

    render: function(x) {
      this.$el.html(this.jst({
        self: this,
        x: x
      }));

      var metrics = this.model.get('metrics');
      this.$('.legend-item').each(function() {
        var $el = $(this),
            name = $el.attr('data-name');

        $el
          .find('.swatch')
          .css('background-color', metrics.get(name).get('color'));
      });

      return this;
    },

    bindings: {
      'hover graph': function(position) {
        this.$el.addClass('hover');
        return this.render(position.x);
      },

      'unhover graph': function() {
        this.$el.removeClass('hover');
        return this.render();
      }
    }
  });

  var GraphHoverMarker = structures.Eventable.extend({
    collisionDistance: 60,

    constructor: function(options) {
      this.graph = options.graph;

      if ('collisionsDistance' in options) {
        this.collisionDistance = options.collisionDistance;
      }

      utils.bindEvents(this.bindings, this);
    },

    collision: function(position, tick) {
      var d = Math.abs(position.svg.x - this.graph.fx(tick));
      return d < this.collisionDistance;
    },

    show: function(position) {
      var marker = this.graph.axis.line
        .selectAll('.hover-marker')
        .data([null]);

      marker.enter().append('g')
        .attr('class', 'hover-marker')
        .call(charts.components.marker)
        .transition()
          .select('text')
          .attr('fill-opacity', 1);

      marker
        .attr('transform', "translate(" + position.svg.x + ", 0)")
        .select('text').text(this.graph.axis.format(position.x));

      var self = this;
      this.graph.axis.line
        .selectAll('g')
        .style('fill-opacity', function(tick) {
          return self.collision(position, tick)
            ? 0
            : 1;
        });

      return this;
    },

    hide: function() {
      this.graph.svg
        .selectAll('.hover-marker')
        .remove();

      this.graph.axis.line
        .selectAll('g')
        .style('fill-opacity', 1);

      return this;
    },

    bindings: {
      'hover graph': function(position) {
        this.show(position);
      },

      'unhover graph': function() {
        this.hide();
      }
    }
  });

  var GraphDots = structures.Eventable.extend({
    size: 3,
    hoverSize: 4,

    constructor: function(options) {
      this.graph = options.graph;
      if ('size' in options) { this.size = options.size; }
      if ('hoverSize' in options) { this.hoverSize = options.hoverSize; }
      utils.bindEvents(this.bindings, this);
    },

    render: function() {
      var metricDots = this.graph.svg
        .selectAll('.metric-dots')
        .data(this.graph.model.get('metrics').models);

      metricDots.enter().append('g')
        .attr('class', 'metric-dots')
        .attr('data-metric', function(d) { return d.get('name'); })
        .style('fill', function(d) { return d.get('color'); });

      metricDots.exit().remove();

      var dot = metricDots
        .selectAll('.dot')
        .data(function(d) { return d.get('datapoints'); });

      dot.enter().append('circle')
        .attr('class', 'dot')
        .attr('r', this.size);

      dot.exit().remove();

      dot
        .attr('cx', this.graph.fx.accessor)
        .attr('cy', this.graph.fy.accessor);

      return this;
    },

    bindings: {
      'hover graph': function(position) {
        var data = this.graph.model
          .get('metrics')
          .map(function(metric) {
            return {
              metric: metric,
              y: metric.valueAt(position.x)
            };
          })
          .filter(function(d) {
            return d.y !== null;
          });

        var dot = this.graph.svg
          .selectAll('.hover-dot')
          .data(data);

        dot.enter().append('circle')
          .attr('class', 'hover-dot')
          .attr('r', 0)
          .style('stroke', function(d) {
            return d.metric.get('color');
          })
          .transition()
            .attr('r', this.hoverSize);

        dot.attr('cx', position.svg.x)
           .attr('cy', this.graph.fy.accessor);
      },

      'unhover graph': function() {
        this.graph.svg
          .selectAll('.hover-dot')
          .remove();
      }
    }
  });

  var GraphLines = structures.Eventable.extend({
    constructor: function(options) {
      this.graph = options.graph;

      this.line = d3.svg.line()
        .interpolate(options.smooth ? 'monotone' : 'linear')
        .x(this.graph.fx.accessor)
        .y(this.graph.fy.accessor);
    },

    render: function() {
      var line = this.graph.svg
        .selectAll('.metric-line')
        .data(this.graph.model.get('metrics').models);

      line.enter().append('path')
        .attr('class', 'metric-line')
        .attr('data-metric', function(d) { return d.get('name'); })
        .style('stroke', function(d) { return d.get('color'); });

      var self = this;
      line.attr('d', function(d) {
        return self.line(d.get('datapoints'));
      });

      return this;
    }
  });

  var GraphView = charts.ChartView.extend({
    dotted: true,
    smooth: true,

    height: 214,
    axisHeight: 24,

    margin: {
      top: 4,
      right: 4,
      left: 4,
      bottom: 0
    },

    initialize: function(options) {
      options = options || {};
      _(options).defaults(options.config);

      if ('margin' in options) { this.margin = options.margin; }
      if ('dotted' in options) { this.dotted = options.dotted; }
      if ('smooth' in options) { this.smooth = options.smooth; }
      if ('height' in options) { this.height = options.height; }
      if ('axisHeight' in options) { this.axisHeight = options.axisHeight; }

      GraphView.__super__.initialize.call(this, {
        dimensions: new charts.Dimensions({
          width: this.$el.width(),
          height: this.height,
          margin: this.margin
        })
      });

      this._setupScales();

      this.lines = new GraphLines({
        graph: this,
        smooth: this.smooth
      });

      this.axis = new charts.AxisView({
        chart: this,
        scale: this.fx,
        height: this.axisHeight
      });

      this.hoverMarker = new GraphHoverMarker({graph: this});
      this.legend = new GraphLegendView({graph: this});
      this.dots = new GraphDots({graph: this});

      utils.bindEvents(this.bindings, this);
    },

    _setupScales: function() {
      var fx = d3.time.scale().range([0, this.dimensions.innerWidth]);
      fx.accessor = function(d) { return fx(d.x); };

      var maxY = this.dimensions.innerHeight - this.axisHeight;
      var fy = d3.scale.linear().range([maxY, 0]);
      fy.accessor = function(d) { return fy(d.y); };

      this.fx = fx;
      this.fy = fy;
    },

    render: function() {
      var domain = this.model.get('domain'),
          range = this.model.get('range'),
          step = this.model.get('step');

      this.fx.domain(domain);
      this.fy.domain(range);

      this.lines.render();

      if (this.dotted) {
        this.dots.render();
      }

      this.axis.render(domain[0], domain[1], step);

      this.legend.render();
      this.$el.append(this.legend.$el);

      return this;
    },

    positionOf: function(coords) {
      var position = {svg: {}};

      position.svg.x = coords.x;
      position.svg.y = coords.y;

      // convert the svg x value to the corresponding time alue, then snap
      // it to the closest timestep
      position.x = utils.snap(
        this.fx.invert(position.svg.x),
        this.model.get('domain')[0],
        this.model.get('step'));

      // shift the svg x value to correspond to the snapped time value
      position.svg.x = this.fx(position.x);

      return position;
    },

    bindings: {
      'mousemove': function(target) {
        var mouse = d3.mouse(target);

        this.trigger('hover', this.positionOf({
          x: mouse[0],
          y: mouse[1]
        }));
      },

      'mouseout': function() {
        this.trigger('unhover');
      },

      'change model': function() {
        this.render();
      }
    }
  });

  return {
    GraphLines: GraphLines,
    GraphDots: GraphDots,
    GraphLegendView: GraphLegendView,
    GraphHoverMarker: GraphHoverMarker,

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
