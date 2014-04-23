diamondash.widgets.pie.views = function() {
  var chart = diamondash.widgets.chart;

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

  return {
    PieDimensions: PieDimensions
  };
}.call(this);
