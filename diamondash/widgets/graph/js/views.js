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
          return self.collision(position, tick);
        });

      return this;
    },

    hide: function() {
      this.graph.svg
        .selectAll('.hover-dot')
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
    hoverSize: 3,

    constructor: function(options) {
      this.graph = options.graph;
      if ('size' in options) { this.size = options.size; }
      if ('hoverSize' in options) { this.hoverSize = options.hoverSize; }
      utils.bindEvents(this.bindings, this);
    },

    render: function() {
      var metricDots = this.graph
        .selectAll('.metric-dots')
        .data(this.graph.model.get('metrics'));

      metricDots.enter().append('g')
        .attr('class', 'metric-dots')
        .style('fill', function(d) { return d.get('color'); });

      metricDots.exit().remove();

      var dot = metricDots
        .selectAll('.dot')
        .data(function(d) { return d.get('datapoints'); });

      dot.enter().append('circle')
        .attr('class', 'dot')
        .attr('r', this.dotSize);

      dot.exit().remove();

      dot
        .attr('cx', this.graph.fx.accessor)
        .attr('cy', this.graph.fy.accessor);
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

        var dot = this.svg
          .selectAll('.hover-dot')
          .data(data);

        dot.enter().append('circle')
          .attr('class', 'hover-dot')
          .style('stroke', function(d) {
            return d.metric.get('color');
          })
          .transition()
            .attr('r', this.hoverSize);

        dot.attr('cx', position.svg.x)
           .attr('cy', this.graph.fy.accessor);
      },

      'unhover graph': function() {
        this.svg
          .selectAll('.hover-dot')
          .remove();
      }
    }
  });

  var GraphLine = structures.Eventable.extend({
    constructor: function(options) {
      this.graph = options.graph;

      this.line = d3.svg.line()
        .interpolate(options.smooth ? 'monotone' : 'linear')
        .x(this.graph.fx.accessor)
        .y(this.graph.fy.accessor);
    },

    render: function() {
      var lines = this.graph
        .selectAll('.line')
        .data(this.graph.model.get('metrics'));

      lines.enter().append('path')
        .attr('class', 'line')
        .style('stroke', function(d) { return d.get('color'); });

      var self = this;
      lines.attr('d', function(d) {
        return self.line(d.get('datapoints'));
      });

      return this;
    }
  });

  var GraphView = charts.ChartView.extend({
    dotted: false,

    smooth: true,

    height: 214,

    margin: {
      top: 4,
      right: 4,
      left: 4,
      bottom: 0
    },

    initialize: function(options) {
      if ('height' in options) { this.height = options.height; }
      if ('margin' in options) { this.margin = options.margin; }
      if ('dotted' in options) { this.dotted = options.dotted; }
      if ('smooth' in options) { this.smooth = options.smooth; }

      GraphView.__super__.initialize.call(this, {
        dimensions: new charts.Dimensions({
          width: this.$el.width(),
          height: this.height,
          margin: this.margin
        })
      });

      this.fx = d3.time.scale().range([0, this.dimensions.innerWidth]);
      this.fx.accessor = function(d) { return this(d.x); };

      this.fy = d3.scale.linear().range([this.dimensions.innerHeight, 0]);
      this.fy.accessor = function(d) { return this(d.y); };

      this.line = new GraphLine({
        graph: this,
        smooth: this.smooth
      });

      this.axis = new charts.AxisView({
        chart: this,
        scale: this.fx
      });

      this.hoverMarker = new GraphHoverMarker({graph: this});
      this.legend = new GraphLegendView({graph: this});

      if (options.dotted) {
        this.dots = new GraphDots({graph: this});
      }
    },

    render: function() {
      var domain = this.model.get('domain'),
          range = this.model.get('range'),
          step = this.model.get('step');

      this.fx.domain(domain);
      this.fy.domain(range);

      this.line.render();
      this.axis.render(domain[0], domain[1], step);
      this.legend.render();

      if (this.dots) {
        this.dots.render();
      }

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

    events: {
      'mouseover': function(e) {
        var mouse = d3.mouse(e.target);

        this.trigger('hover', this.positionOf({
          x: mouse[0],
          y: mouse[1]
        }));
      },

      'mouseout': function() {
        this.trigger('unhover');
      }
    }
  });

  return {
    GraphLine: GraphLine,
    GraphDots: GraphDots,
    GraphLegendView: GraphLegendView,
    GraphHoverMarker: GraphHoverMarker,

    GraphView: GraphView
  };
}.call(this);
