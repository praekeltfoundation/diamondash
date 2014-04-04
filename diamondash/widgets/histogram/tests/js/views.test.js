describe("diamondash.widgets.histogram", function() {
  describe("HistogramView", function() {
    var histogram;

    beforeEach(function() {
      histogram = new views.HistogramView({
        el: $('<div>')
          .width(960)
          .height(64),
        model: new models.HistogramModel(
          fixtures.get('diamondash.widgets.histogram.models.HistogramModel:simple'))
      });
    });
  });
});
