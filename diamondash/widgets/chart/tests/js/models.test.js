describe("diamondash.widgets.chart.models", function() {
  var utils = diamondash.test.utils,
      fixtures = diamondash.test.fixtures,
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

    describe(".xMin()", function() {
      it("should calculate its minimum x value", function() {
        assert.deepEqual(model.xMin(), 0);
      });
    });

    describe(".xMax()", function() {
      it("should calculate its maximum x value", function() {
        assert.deepEqual(model.xMax(), 3);
      });
    });

    describe(".domain()", function() {
      it("should calculate its domain", function() {
        assert.deepEqual(model.domain(), [0, 3]);
      });
    });

    describe(".yMin()", function() {
      it("should calculate its minimum x value", function() {
        assert.deepEqual(model.yMin(), 1);
      });
    });

    describe(".yMax()", function() {
      it("should calculate its maximum x value", function() {
        assert.deepEqual(model.yMax(), 5);
      });
    });

    describe(".range()", function() {
      it("should calculate its range", function() {
        assert.deepEqual(model.range(), [1, 5]);
      });
    });
  });

  describe("ChartMetricCollection", function() {
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

  describe(".ChartModel", function() {
    var model;

    beforeEach(function() {
      model = new models.ChartModel(
        fixtures.get('diamondash.widgets.chart.models.ChartModel:simple'));
    });

    describe(".xMin()", function() {
      it("should calculate its minimum x value", function() {
        assert.deepEqual(model.xMin(), 1340875995000);
      });
    });

    describe(".xMax()", function() {
      it("should calculate its maximum x value", function() {
        assert.deepEqual(model.xMax(), 1340877495000);
      });
    });

    describe(".domain()", function() {
      it("should calculate its domain", function() {
        assert.deepEqual(model.domain(), [1340875995000, 1340877495000]);
      });
    });

    describe(".yMin()", function() {
      it("should calculate its minimum y value", function() {
        assert.deepEqual(model.yMin(), 2);
      });
    });

    describe(".yMax()", function() {
      it("should calculate its maximum y value", function() {
        assert.deepEqual(model.yMax(), 24);
      });
    });

    describe(".range()", function() {
      it("should calculate its range", function() {
        assert.deepEqual(model.range(), [2, 24]);
      });
    });
  });
});
