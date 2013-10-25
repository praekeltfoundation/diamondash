describe("diamondash.widgets.chart.models", function() {
  var utils = diamondash.test.utils,
      models = diamondash.widgets.chart.models;

  afterEach(function() {
    utils.unregisterModels();
  });

  describe("ChartMetricModel", function() {
    var model;

    beforeEach(function() {
      model = new models.ChartMetricModel({
        datapoints: [
          {x: 0, y: 1},
          {x: 1, y: 2},
          {x: 3, y: 5}]
      });
    });

    describe(".lastValue()", function() {
      it("should return the last value.", function() {
        assert.equal(model.lastValue(), 5);
      });

      it("should return null for empty datapoints.", function() {
        model.set('datapoints', []);
        assert.equal(model.lastValue(), null);
      });

      it("should return null on undefined y values.", function() {
        model.set('datapoints', [{x: 0}]);
        assert.equal(model.lastValue(), null);
      });
    });

    describe(".valueAt()", function() {
      it("should return a value if it exists at x", function() {
        assert.equal(model.valueAt(1), 2);
      });

      it("should return null if no value exists at x", function() {
        assert.equal(model.valueAt(2), null);
      });

      it("should return null for empty datapoints", function() {
        model.set('datapoints', []);
        assert.equal(model.valueAt(2), null);
      });
    });
  });

  describe("GraphMetricCollection", function() {
    var collection;

    beforeEach(function() {
      collection = new models.ChartMetricCollection();
    });

    describe("when a metric is added", function() {
      it("should assign it a color", function(done) {
        collection.on('add', function(metric) {
          assert.equal(metric.get('color'), '#1f77b4');
          done();
        });

        collection.add({name: 'foo'});
      });
    });
  });
});
