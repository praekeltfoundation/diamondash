var d3 = require('d3'), 
    Backbone = require('backbone'),
    widget = require("widgets/widget/widget"),
    exports = module.exports = {};

exports.GraphWidgetModel = widget.WidgetModel.extend({
  isStatic: false,

  initialize: function(options) {
    var self = this,
        metrics = new exports.GraphWidgetMetricCollection(options.metrics);

    metrics
      .on(
        'all',
        function(eventName) { self.trigger(eventName + ':metrics'); })
      .on(
        'change',
        function() { self.trigger('change'); });

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

    this.get('metrics').update(data.metrics);
  }
});


var maxColors = 10,
    color = d3.scale.category10().domain(d3.range(maxColors)),
    colorCount = 0;

var nextColor = function() {
  return color(colorCount++ % maxColors);
};

exports.GraphWidgetMetricModel = Backbone.Model.extend({
  idAttribute: 'name',

  initialize: function(options) {
    if (typeof options.datapoints === 'undefined') {
      this.set('datapoints', []);
      if (!this.has('color')) {
        this.set('color', nextColor());
      }
    }
  }
});

exports.GraphWidgetMetricCollection = Backbone.Collection.extend({
  model: exports.GraphWidgetMetricModel
});

exports.GraphWidgetView = widget.WidgetView.extend({
  height: 180,
  margin: {top: 4, right: 4, bottom: 4, left: 4},

  initialize: function(options) {
    var margin = this.margin,
        width, height,
        x, y,
        xAxis, yAxis,
        chart;

    this.width = width = this.$el.width();
    height = this.height;

    this.chartWidth = width - margin.left - margin.right;
    this.chartHeight = height - margin.top - margin.bottom;

    this.x = x = d3.time.scale().range([0, this.chartWidth]);
    this.y = y = d3.scale.linear().range([this.chartHeight, 0]);

    xAxis = d3.svg.axis()
      .scale(x)
      .orient('bottom');

    yAxis = d3.svg.axis()
      .scale(y)
      .orient('left');

    this.line = d3.svg.line()
      .interpolate("basis")
      .x(function(d) { return x(d.x); })
      .y(function(d) { return y(d.y); });

    this.svg = d3.select(this.el).append('svg')
        .attr('width', width)
        .attr('height', height)
      .append('g')
        .attr('transform', "translate(" + margin.left + "," + margin.top + ")");

    this.chart = chart = this.svg.append('g')
      .attr('class', 'chart');

    chart.append("g")
        .attr('class', 'x axis')
        .attr('transform', "translate(0," + this.chartHeight + ")")
        .call(xAxis);

    chart.append('g')
        .attr('class', 'y axis')
        .call(yAxis);

    this.model.on('change', this.render, this);
  },

  render: function() {
    var model = this.model,
        line = this.line,
        metrics = model.get('metrics').toJSON(),
        domain = model.get('domain'),
        range = model.get('range');

    this.x.domain(domain);
    this.y.domain(range);

    var chartLines = this.chart.selectAll('.line')
      .data(metrics, function(d) { return d.name; });

    chartLines.enter().append('path')
      .attr('class', 'line')
      .style('stroke', function(d) { return d.color; });

    chartLines
      .attr('d', function(d) { return line(d.datapoints); });
  }
});
