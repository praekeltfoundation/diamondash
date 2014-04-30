diamondash.widgets.histogram.views = function() {
  var chart = diamondash.widgets.chart,
      widgets = diamondash.widgets;

  var HistogramView = chart.views.XYChartView.extend({
    height: 278,

    initialize: function() {
      HistogramView.__super__.initialize.call(this);
    },

    render: function() {
      HistogramView.__super__.render.call(this);
      this.$el.append($(this.svg.node()));
      return this;
    }
  });

  widgets.registry.views.add('histogram', HistogramView);

  return {
    HistogramView: HistogramView
  };
}.call(this);
