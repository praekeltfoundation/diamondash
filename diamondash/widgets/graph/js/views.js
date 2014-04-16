diamondash.widgets.graph.views = function() {
  var widgets = diamondash.widgets,
      utils = diamondash.utils,
      structures = diamondash.components.structures,
      chart = diamondash.widgets.chart;

  var GraphLegendView = Backbone.View.extend({
    className: 'legend',

    jst: JST['diamondash/widgets/graph/legend.jst'],

    initialize: function(options) {
      this.graph = options.graph;
      this.model = this.graph.model;
      utils.bindEvents(this.bindings, this);
    },

    valueOf: function(metricId, x) {
      var metric = this.model.get('metrics').get(metricId);
      var v = typeof x == 'undefined'
        ? metric.lastValue()
        : metric.valueAt(x);

        return v === null
          ? this.model.get('default_value')
          : v;
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
            id = $el.attr('data-metric-id');

        $el
          .find('.swatch')
          .css('background-color', metrics.get(id).get('color'));
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

  var GraphView = chart.views.ChartView.extend({
    height: 214,
    axisHeight: 24,

    margin: {
      top: 4,
      right: 4,
      left: 4,
      bottom: 0
    },

    id: function() {
      return this.model.id;
    },

    initialize: function() {
      GraphView.__super__.initialize.call(this, {
        dims: new chart.views.ChartDimensions({
          height: this.height,
          margin: this.margin
        })
      });

      var fx = d3.time.scale();
      fx.accessor = function(d) { return fx(d.x); };
      this.fx = fx;

      var fy = d3.scale.linear();
      fy.accessor = function(d) { return fy(d.y); };
      this.fy = fy;

      this.lines = new GraphLines({graph: this});

      this.axis = new chart.views.ChartAxisView({
        chart: this,
        scale: this.fx,
        height: this.axisHeight
      });

      this.hoverMarker = new GraphHoverMarker({graph: this});
      this.legend = new GraphLegendView({graph: this});
      this.dots = new GraphDots({graph: this});

      utils.bindEvents(this.bindings, this);
    },

    resetScales: function() {
      var maxY = this.dims.innerHeight() - this.axisHeight;
      this.fy.range([maxY, 0]);
      this.fx.range([0, this.dims.innerWidth()]);
    },

    render: function() {
      this.dims.set('width', this.$el.width());
      this.resetScales();

      var domain = this.model.domain();
      this.fx.domain(domain);
      this.fy.domain(this.model.range());

      this.lines.render();

      if (this.model.get('dotted')) {
        this.dots.render();
      }

      var step = this.model.get('bucket_size');
      this.axis.render(domain[0], domain[1], step);

      this.legend.render();

      this.$el
        .append($(this.svg.node()))
        .append(this.legend.$el);

      return this;
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

      'sync model': function() {
        this.render();
      }
    }
  });

  widgets.registry.views.add('graph', GraphView);

  return {
    GraphLines: GraphLines,
    GraphDots: GraphDots,
    GraphLegendView: GraphLegendView,
    GraphHoverMarker: GraphHoverMarker,

    GraphView: GraphView
  };
}.call(this);
