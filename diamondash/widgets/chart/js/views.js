diamondash.widgets.chart.views = function() {
  var structures = diamondash.components.structures,
      widgets = diamondash.widgets,
      widget = diamondash.widgets.widget,
      utils = diamondash.utils;

  var components = {};

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

  var ChartDimensions = Backbone.Model.extend({
    defaults: {
      height: 0,
      width: 0,
      offset: {
        x: 0,
        y: 0
      }
    },

    height: function() {
      return this.get('height');
    },

    width: function() {
      return this.get('width');
    },

    offset: function() {
      return this.get('offset');
    }
  });

  var ChartAxisView = structures.Eventable.extend({
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

      this.line = this.chart.canvas.append("g")
        .attr('class', 'axis')
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
        p = this.chart.dims.width() - this.height;
        return "translate(" + p + ", 0)";
      }

      p = this.chart.dims.height() - this.height;
      return "translate(0, " + p + ")";
    },

    format: function() {
      var format = d3.time.format.utc("%d-%m %H:%M");
      return function(t) { return format(new Date(t)); };
    }(),

    tickCount: function() {
      var count = Math.floor(this.chart.dims.width() / this.markerWidth);
      return Math.max(0, count);
    },

    tickValues: function(start, end, step) {
      start = start || 0;
      end = end || 0;
      step = step || 1;

      var n = (end - start) / step;
      var m = _(this).result('tickCount');
      var i = 1;

      while (Math.floor(n / i) > m) { i++; }

      var values = d3.range(start, end, step * i);
      values.push(end);

      return values;
    },

    render: function(start, end, step) {
      this.line.attr('transform', this._translation());
      this.axis.tickValues(this.tickValues(start, end, step));
      this.line.call(this.axis);
      return this;
    }
  });

  var ChartView = widget.WidgetView.extend({
    className: 'chart',

    initialize: function(options) {
      options = options || {};
      this.dims = options.dims || new ChartDimensions();

      this.svg = d3.select(this.el).append('svg');
      this.canvas = this.svg.append('g');

      var self = this;
      this.overlay = this.canvas.append('rect')
        .attr('class', 'event-overlay')
        .attr('fill-opacity', 0)
        .on('mousemove', function() { self.trigger('mousemove', this); })
        .on('mouseout', function() { self.trigger('mouseout', this); });

      this.refreshDims();

      this.dims.on('change', function() {
        this.refreshDims();
      }, this);
    },

    refreshDims: function() {
      var offset = this.dims.offset();

      this.canvas.attr(
        'transform',
        'translate(' + offset.x + ',' + offset.y + ')'); 

      this.svg
        .attr('width', this.dims.width())
        .attr('height', this.dims.height());

      this.overlay
        .attr('width', this.dims.width())
        .attr('height', this.dims.height());
    }
  });

  var XYChartView = ChartView.extend({
    height: 214,
    axisHeight: 24,

    initialize: function() {
      XYChartView.__super__.initialize.call(this, {
        dims: new ChartDimensions({height: this.height})
      });

      var fx = d3.time.scale();
      fx.accessor = function(d) { return fx(d.x); };
      this.fx = fx;

      var fy = d3.scale.linear();
      fy.accessor = function(d) { return fy(d.y); };
      this.fy = fy;

      this.axis = new ChartAxisView({
        chart: this,
        scale: this.fx,
        height: this.axisHeight
      });

      utils.bindEvents(XYChartView.prototype.bindings, this);
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
      }
    },

    render: function() {
      this.dims.set('width', this.$el.width());

      var maxY = this.dims.height() - this.axisHeight;
      this.fy.range([maxY, 0]);
      this.fx.range([0, this.dims.width()]);

      var domain = this.model.domain();
      this.fx.domain(domain);
      this.fy.domain(this.model.range());

      var step = this.model.get('bucket_size');
      this.axis.render(domain[0], domain[1], step);
    },

    positionOf: function(coords) {
      var position = {svg: {}};

      position.svg.x = coords.x;
      position.svg.y = coords.y;

      var min = this.model.xMin();
      if (min === null) {
        position.x = null;
      }
      else {
        // convert the svg x value to the corresponding time value, then snap
        // it to the closest timestep
        position.x = utils.snap(
          this.fx.invert(position.svg.x),
          min,
          this.model.get('bucket_size'));

        // shift the svg x value to correspond to the snapped time value
        position.svg.x = this.fx(position.x);
      }

      return position;
    }
  });

  widgets.registry.views.add('chart', ChartView);

  return {
    components: components,
    ChartAxisView: ChartAxisView,
    ChartView: ChartView,
    XYChartView: XYChartView,
    ChartDimensions: ChartDimensions
  };
}.call(this);
