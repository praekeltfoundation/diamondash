var widgets = diamondash.widgets;

widgets.GraphWidgetModel = widgets.WidgetModel.extend({
  isStatic: false,

  initialize: function(options) {
    options = options || {};

    var self = this,
        metrics = new widgets.GraphWidgetMetricCollection(
          options.metrics || []);

    metrics
      .on('all', function(eventName) { self.trigger(eventName + ':metrics'); })
      .on('change', function() { self.trigger('change'); });

    this.set({
      metrics: metrics,
      domain: 0,
      range: 0
    });
  },

  parse: function(data) {
    this.set({
      domain: data.domain,
      range: data.range
    }, {silent: true});

    this.get('metrics').update(data.metrics, {merge: true});
  }
});


var maxColors = 10,
    color = d3.scale.category10().domain(d3.range(maxColors)),
    colorCount = 0,
    nextColor = function() { return color(colorCount++ % maxColors); };

widgets.GraphWidgetMetricModel = Backbone.Model.extend({
  idAttribute: 'name',

  initialize: function(options) {
    if (typeof options.datapoints === 'undefined') {
      this.set('datapoints', []);
      if (!this.has('color')) {
        this.set('color', nextColor());
      }
    }
  },

  coordsAt: function(i) {
    return this.get('datapoints')[i] || {x: 0, y: 0};
  }
});

widgets.GraphWidgetMetricCollection = Backbone.Collection.extend({
  model: widgets.GraphWidgetMetricModel
});

var _formatTime = d3.time.format("%d-%m %H:%M");

widgets.GraphWidgetView = widgets.WidgetView.extend({
  svgHeight: 194,
  axisHeight: 24,
  timeMarkerWidth: 128,
  margin: {top: 4, right: 4, bottom: 4, left: 4},

  formatTime: function(x) { return _formatTime(new Date(x * 1000)); },

  initialize: function(options) {
    var self = this,
        metrics = this.model.get('metrics').toJSON(),
        d3el = d3.select(this.el);

    // Chart Setup
    // -----------
    this.width = this.$el.width();

    var margin = this.margin,
        chartWidth = this.width - margin.left - margin.right,
        chartHeight = this.svgHeight
          - this.axisHeight - margin.top - margin.bottom;

    this.width = this.$el.width();

    var svg = d3el.append('svg')
        .attr('width', this.width)
        .attr('height', this.svgHeight)
      .append('g')
        .attr('transform', "translate(" + margin.left + "," + margin.top + ")");

    var x, y;
    this.x = x = d3.time.scale().range([0, chartWidth]);
    this.y = y = d3.scale.linear().range([chartHeight, 0]);

    this.maxTicks = Math.floor(chartWidth / this.timeMarkerWidth);
    this.xAxis = d3.svg.axis()
      .scale(x)
      .orient('bottom')
      .tickFormat(d3.time.format("%d-%m %H:%M"))
      .ticks(this.maxTicks);

    this.line = d3.svg.line()
      .interpolate("basis")
      .x(function(d) { return x(d.x); })
      .y(function(d) { return y(d.y); });

    var chart = this.chart = svg.append('g')
      .attr('class', 'chart')
      .attr('height', chartHeight);

    this.xAxisLine = svg.append("g")
      .attr('class', 'x axis')
      .attr('transform',
            "translate(0," + (this.svgHeight - this.axisHeight) + ")")
      .call(this.xAxis);

    // Legend Setup
    // -----------
    var legend = d3el.append('ul')
      .attr('class', 'legend');

    var legendItem = this.legendItem = legend.selectAll('.legend-item')
      .data(metrics, function(d) { return d.name; })
      .enter()
      .append('li')
        .attr('class', 'legend-item');

    this.legendItemSwatch = legendItem.append('span')
      .attr('class', 'legend-item-swatch')
      .style('background-color', function(d) { return d.color; });

    this.legendItemTitleLabel = legendItem.append('span')
      .attr('class', 'legend-item-title-label')
      .text(function(d) { return d.title; });

    this.legendItemValueLabel = legendItem.append('span')
      .attr('class', 'legend-item-value-label');

    this.formatNumber = d3.format(".3s");

    // Model-View Bindings Setup
    // -------------------------
    this.model.on('change', this.render, this);
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
        metrics = model.get('metrics').toJSON(),
        domain = model.get('domain'),
        range = model.get('range'),
        bucketSize = model.get('bucketSize'),
        formatNumber = this.formatNumber;

    this.x.domain(domain);
    this.y.domain(range);

    this.xAxis.tickValues(this.genTickValues.apply(
      this, domain.concat([bucketSize])));
    this.xAxisLine.call(this.xAxis);

    var chartLines = this.chart.selectAll('.line')
      .data(metrics, function(d) { return d.name; });

    chartLines.enter().append('path')
      .attr('class', 'line')
      .style('stroke', function(d) { return d.color; });

    chartLines.attr('d', function(d) { return line(d.datapoints); });

    this.legendItemTitleLabel.text(function(d) { return d.title + ": "; });

    // format the last metric value displayed for each metric
    this.legendItemValueLabel.data(metrics, function(d) { return d.name; })
      .text(function(d) {
        var datapoints = d.datapoints;
        return datapoints.length > 0
          ? formatNumber(datapoints[datapoints.length - 1].y)
          : 0;
    });
  }
});
