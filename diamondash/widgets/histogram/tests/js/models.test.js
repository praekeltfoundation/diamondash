describe("diamondash.widgets.histogram.models", function() {
  var utils = diamondash.test.utils,
      fixtures = diamondash.test.fixtures,
      models = diamondash.widgets.histogram.models;

  afterEach(function() {
    utils.unregisterModels();
  });

  describe("HistogramModel", function() {
    var model;

    beforeEach(function() {
      model = new models.HistogramModel(
        fixtures.get('diamondash.widgets.histogram.models.HistogramModel:simple'));
    });

    describe(".range()", function() {
      it("should calculate its range as 0 to its highest y value", function() {
        assert.deepEqual(model.range(), [0, 24]);
      });
    });
  });
});
