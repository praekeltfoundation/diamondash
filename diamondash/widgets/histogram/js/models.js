diamondash.widgets.histogram.models = function() {
  var widgets = diamondash.widgets,
      chart = diamondash.widgets.chart;

  var HistogramModel = chart.models.ChartModel.extend({
  });

  widgets.registry.models.add('histogram', HistogramModel);

  return {
    HistogramModel: HistogramModel
  };
}.call(this);
