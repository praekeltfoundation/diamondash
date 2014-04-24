diamondash.widgets.graph.views = function() {
  var widgets = diamondash.widgets,
      utils = diamondash.utils,
      structures = diamondash.components.structures,
      chart = diamondash.widgets.chart;

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
        .call(chart.views.components.marker)
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
      this.graph.canvas
        .selectAll('.hover-marker')
        .remove();

      this.graph.axis.line
        .selectAll('g')
        .style('fill-opacity', 1);

      return this;
    },

    bindings: {
      'hover graph': function(position) {
        if (position.x !== null) {
          this.show(position);
        }
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
      var metricDots = this.graph.canvas
        .selectAll('.metric-dots')
        .data(this.graph.model.get('metrics').models);

      metricDots.enter().append('g')
        .attr('class', 'metric-dots')
        .attr('data-metric-id', function(d) { return d.get('id'); })
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

        var dot = this.graph.canvas
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
        this.graph.canvas
          .selectAll('.hover-dot')
          .remove();
      }
    }
  });

  var GraphLines = structures.Eventable.extend({
    constructor: function(options) {
      this.graph = options.graph;

      this.line = d3.svg.line()
        .x(this.graph.fx.accessor)
        .y(this.graph.fy.accessor);
    },

    render: function() {
      this.line.interpolate(this.graph.model.get('smooth')
        ? 'monotone'
        : 'linear');

      var line = this.graph.canvas
        .selectAll('.metric-line')
        .data(this.graph.model.get('metrics').models);

      line.enter().append('path')
        .attr('class', 'metric-line')
        .attr('data-metric-id', function(d) { return d.get('id'); })
        .style('stroke', function(d) { return d.get('color'); });

      var self = this;
      line.attr('d', function(d) {
        return self.line(d.get('datapoints'));
      });

      return this;
    }
  });

  var GraphView = chart.views.XYChartView.extend({
    height: 214,
    axisHeight: 24,

    initialize: function() {
      GraphView.__super__.initialize.call(this);
      this.legend = new chart.views.ChartLegendView({chart: this});
      this.lines = new GraphLines({graph: this});
      this.hoverMarker = new GraphHoverMarker({graph: this});
      this.dots = new GraphDots({graph: this});
    },

    render: function() {
      GraphView.__super__.render.call(this);
      this.lines.render();

      if (this.model.get('dotted')) {
        this.dots.render();
      }

      this.legend.render();

      this.$el
        .append($(this.svg.node()))
        .append(this.legend.$el);

      return this;
    }
  });

  widgets.registry.views.add('graph', GraphView);

  return {
    GraphLines: GraphLines,
    GraphDots: GraphDots,
    GraphHoverMarker: GraphHoverMarker,
    GraphView: GraphView
  };
}.call(this);
