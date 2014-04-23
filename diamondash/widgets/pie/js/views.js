diamondash.widgets.pie.views = function() {
  var chart = diamondash.widgets.chart,
      widgets = diamondash.widgets,
      utils = diamondash.utils;

  var PieDimensions = chart.views.ChartDimensions.extend({
    defaults: _.extend({
      scale: 0.6
    }, chart.views.ChartDimensions.prototype.defaults),

    scale: function() {
      return this.get('scale');
    },

    height: function() {
      return this.width() * this.scale();
    },

    radius: function() {
      return (this.width() / 2) * this.scale();
    },

    offset: function() {
      return {
        x: this.width() / 2,
        y: this.radius()
      };
    }
  });

  var PieView = chart.views.ChartView.extend({
    id: function() {
      return this.model.id;
    },

    margin: {
      top: 4,
      right: 4,
      left: 4,
      bottom: 0
    },

    bindings: {
      'sync model': function() {
        this.render();
      }
    },

    initialize: function() {
      PieView.__super__.initialize.call(this, {
        dims: new PieDimensions({margin: this.margin})
      });

      this.arc = d3.svg.arc();

      this.pie = d3.layout.pie().value(function(d) {
        var datapoint = d.get('datapoints')[0];
        return datapoint
          ? datapoint.y
          : 1;
      });

      utils.bindEvents(this.bindings, this);
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
