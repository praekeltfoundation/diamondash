diamondash.widgets.pie.views = function() {
  var chart = diamondash.widgets.chart,
      widgets = diamondash.widgets;

  var PieDimensions = chart.views.ChartDimensions.extend({
    innerWidth: function() {
      var margin = this.margin();
      return this.width() - margin.left - margin.right;
    },

    height: function() {
      return this.width();
    },

    radius: function() {
      return this.innerWidth() / 2;
    },

    offset: function() {
      var radius = this.radius();

      return {
        x: radius,
        y: radius
      };
    }
  });

  var PieView = chart.views.ChartView.extend({
    jst: JST['diamondash/widgets/pie/layout.jst'],

    initialize: function() {
      PieView.__super__.initialize.call(this, {
        dims: new PieDimensions()
      });

      this.arc = d3.svg.arc();

      this.pie = d3.layout.pie().value(function(d) {
        return d.lastValue();
      });

      this.legend = new chart.views.ChartLegendView({chart: this});
    },

    refreshChartDims: function() {
      var $chart = this.$('.chart');
      var width = $chart.width();
      $chart.height(width);
      this.dims.set({width: width});
    },

    renderChart: function() {
      var metrics = this.model
        .get('metrics')
        .filter(function(m) {
          return m.lastValue() > 0;
        });

      this.arc
        .outerRadius(this.dims.radius())
        .innerRadius(0);

      var arc = this.canvas.selectAll('.arc')
        .data(this.pie(metrics), function(d) {
          return d.data.id;
        });

      arc.enter().append('path')
        .attr('class', 'arc')
        .style('fill', function(d) {
          return d.data.get('color');
        });

      arc.attr('d', this.arc);
      arc.exit().remove();

      this.$('.chart').html(this.svg.node());
    },

    render: function() {
      this.$el.html(this.jst());
      this.refreshChartDims();
      this.renderChart();
      this.legend.setElement(this.$('.legend'));
      this.legend.render();
    }
  });

  widgets.registry.views.add('pie', PieView);

  return {
    PieView: PieView,
    PieDimensions: PieDimensions
  };
}.call(this);
