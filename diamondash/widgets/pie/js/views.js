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
        var datapoint = d.get('datapoints')[0];
        return datapoint
          ? datapoint.y
          : 1;
      });
    },

    render: function() {
      this.dims.set({width: this.$el.width()});

      this.arc
        .outerRadius(this.dims.radius())
        .innerRadius(0);

      var g = this.canvas.selectAll('.arc')
        .data(this.pie(this.model.get('metrics').models))
        .enter().append('g')
          .attr('class', 'arc');

      g.append('path')
        .attr('d', this.arc)
        .style('fill', function(d) {
          return d.data.get('color');
        });

      this.$el.append($(this.svg.node()));
    }
  });

  widgets.registry.views.add('pie', PieView);

  return {
    PieView: PieView,
    PieDimensions: PieDimensions
  };
}.call(this);
