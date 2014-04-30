diamondash.widgets.pie.models = function() {
  var widgets = diamondash.widgets,
      chart = diamondash.widgets.chart;

  var PieModel = chart.models.ChartModel.extend({
  });

  widgets.registry.models.add('pie', PieModel);

  return {
    PieModel: PieModel
  };
}.call(this);
