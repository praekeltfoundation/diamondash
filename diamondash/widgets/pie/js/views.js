diamondash.widgets.pie.views = function() {
  var chart = diamondash.widgets.chart,
      widgets = diamondash.widgets;

  var PieDimensions = chart.views.ChartDimensions.extend({
    height: function() {
      return this.width();
    },

    radius: function() {
      return this.width() / 2;
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
    initialize: function() {
      PieView.__super__.initialize.call(this, {
        dims: new PieDimensions()
      });

      this.arc = d3.svg.arc();

      this.pie = d3.layout.pie().value(function(d) {
        return d.lastValue();
      });
    },

    render: function() {
      var metrics = this.model
        .get('metrics')
        .filter(function(m) {
          return m.lastValue() > 0;
        });

      this.dims.set({width: this.$el.width()});

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
      this.$el.append($(this.svg.node()));
    }
  });

  widgets.registry.views.add('pie', PieView);

  return {
    PieView: PieView,
    PieDimensions: PieDimensions
  };
}.call(this);
