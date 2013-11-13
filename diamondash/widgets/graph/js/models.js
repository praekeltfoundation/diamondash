diamondash.widgets.graph.models = function() {
  var widgets = diamondash.widgets,
      chart = diamondash.widgets.chart;

  var GraphModel = chart.models.ChartModel.extend({
    defaults: _({
      dotted: false,
      smooth: false
    }).defaults(chart.models.ChartModel.prototype.defaults)
  });

  widgets.registry.models.add('graph', GraphModel);

  return {
    GraphModel: GraphModel
  };
}.call(this);
