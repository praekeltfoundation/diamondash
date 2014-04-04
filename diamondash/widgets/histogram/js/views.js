diamondash.widgets.histogram.views = function() {
  var HistogramView = Backbone.View.extend({
  });

  widgets.registry.views.add('histogram', HistogramView);

  return {
    HistogramView: HistogramView
  };
}.call(this);
