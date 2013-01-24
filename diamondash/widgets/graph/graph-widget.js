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

    this.get('metrics').update(data.metrics, {merge: true});
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
  svgHeight: 180,
  margin: {top: 4, right: 4, bottom: 4, left: 4},

  initialize: function(options) {
    var margin = this.margin,
        width,
        svgHeight,
        x, y,
        xAxis, yAxis,
        d3el,
        svg, chart,
        metrics,
        legend, legendItem;

    metrics = this.model.get('metrics').toJSON();
    d3el = d3.select(this.el);
    this.width = width = this.$el.width();

    // Chart Setup
    // -----------
    svgHeight = this.svgHeight;

    svg = d3el.append('svg')
        .attr('width', width)
        .attr('height', svgHeight)
      .append('g')
        .attr('transform', "translate(" + margin.left + "," + margin.top + ")");
    this.chartWidth = width - margin.left - margin.right;
    this.chartHeight = svgHeight - margin.top - margin.bottom;

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

    this.chart = chart = svg.append('g')
      .attr('class', 'chart');

    chart.append("g")
      .attr('class', 'x axis')
      .attr('transform', "translate(0," + this.chartHeight + ")")
      .call(xAxis);

    chart.append('g')
      .attr('class', 'y axis')
      .call(yAxis);

    // Legend Setup
    // -----------
    legend = d3el.append('ul')
      .attr('class', 'legend');

    this.legendItem = legendItem = legend.selectAll('.legend-item')
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
        
    // Model-View Bindings Setup
    // -------------------------
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

    this.legendItemTitleLabel.text(function(d) { return d.title + ": "; });
    this.legendItemValueLabel.data(metrics, function(d) { return d.name; })
      .text(function(d) {
        return (d.datapoints.length > 0 ? d.datapoints.slice(-1)[0].y : 0);
    });
  }
});
