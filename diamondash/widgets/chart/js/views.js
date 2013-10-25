diamondash.widgets.chart.views = function() {
  var structures = diamondash.components.structures,
      utils = diamondash.utils,
      widgets = diamondash.widgets,
      widget = diamondash.widgets.widget;

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

  var ChartDimensions = structures.Extendable.extend({
    height: 0,
    width: 0,

    margin: {
      top: 0,
      right: 0,
      bottom: 0,
      left: 0
    },

    constructor: function(options) {
      this.set(options);
    },

    set: function(options) {
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
      var width = this.chart.dimensions.width;
      var count = Math.floor(width / this.markerWidth);

      return Math.max(0, count);
    },

    tickValues: function(start, end, step) {
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
      this.dimensions = new ChartDimensions(options.dimensions);

      this.svg = d3.select(this.el).append('svg');
      this.canvas = this.svg.append('g');

      var self = this;
      this.overlay = this.canvas.append('rect')
        .attr('class', 'event-overlay')
        .attr('fill-opacity', 0)
        .on('mousemove', function() { self.trigger('mousemove', this); })
        .on('mouseout', function() { self.trigger('mouseout', this); });
    },

    render: function() {
      this.svg
        .attr('width', this.dimensions.width)
        .attr('height', this.dimensions.height);

      this.canvas
        .attr('transform', 'translate('
          + this.dimensions.margin.left
          + ','
          + this.dimensions.margin.top + ')');

      this.overlay
        .attr('width', this.dimensions.width)
        .attr('height', this.dimensions.height);

      return this;
    }
  });

  widgets.registry.views.add('chart', ChartView);

  return {
    components: components,
    AxisView: AxisView,
    ChartView: ChartView,
    ChartDimensions: ChartDimensions
  };
}.call(this);
