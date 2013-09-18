describe("diamondash.widgets.graph", function() {
  describe("GraphModel", function() {
    var GraphModel = diamondash.widgets.graph.GraphModel;

    it("should react to its metrics' events", function() {
        var model = new GraphModel({
          metrics: [
            {name: 'm1', title: 'metric 1'},
            {name: 'm2', title: 'metric 2'}]
        });

        var modelChanged = false,
            metricsChanged = false,
            metricsAdded = false,
            metricsRemoved = false,
            metricsReset = false;

        var metrics = model.get('metrics');

        model.on('change', function() { modelChanged = true; });
        model.on('change:metrics', function() { metricsChanged = true; });
        metrics.set({name: 'm1', title: 'aaah'});
        assert(modelChanged);
        assert(metricsChanged);

        model.on('add:metrics', function() { metricsAdded = true; });
        metrics.add({name: 'm3', title: 'larp'});
        assert(metricsAdded);

        model.on('remove:metrics', function() { metricsRemoved = true; });
        metrics.remove(metrics.get('m1'));
        assert(metricsRemoved);

        model.on('reset:metrics', function() { metricsReset = true; });
        metrics.reset();
        assert(metricsReset);
      });

      describe(".parse()", function() {
        it("should update the model's metrics with new datapoints", function() {
          var model = new GraphModel({
            'metrics': [
              {name: 'm1', datapoints: [{x: 0, y: 1}, {x: 1, y: 3}]},
              {name: 'm2', datapoints: [{x: 0, y: 8}, {x: 1, y: 9}]}]
          });

          model.parse({
            'domain': [3, 5],
            'range': [3, 11],
            'metrics': [
               {name: 'm1', datapoints: [{x: 3, y: 9}, {x: 5, y: 3}]},
               {name: 'm2', datapoints: [{x: 3, y: 8}, {x: 5, y: 11}]}]
          });

          assert.deepEqual(model.get('domain'), [3, 5]);
          assert.deepEqual(model.get('range'), [3, 11]);

          assert.deepEqual(
            model.get('metrics')
                 .get('m1')
                 .get('datapoints'),
            [{x: 3, y: 9}, {x: 5, y: 3}]);

          assert.deepEqual(
            model.get('metrics')
                 .get('m2')
                 .get('datapoints'),
            [{x: 3, y: 8}, {x: 5, y: 11}]);
        });
    });
  });

  describe("GraphView", function() {
    var GraphModel = diamondash.widgets.graph.GraphModel,
        GraphView = diamondash.widgets.graph.GraphView;

    describe(".genTickValues()", function() {
      it("should generate the correct number of tick values", function() {
        var model = new GraphModel();
        var view = new GraphView({model: model});
        view.maxTicks = 8;
        assert.deepEqual(view.genTickValues(2, 96, 5), d3.range(2, 96, 5 * 3));
        assert.deepEqual(view.genTickValues(3, 98, 5), d3.range(3, 98, 5 * 3));
      });
    });

    describe("snapX", function() {
      it("should snap to the closest x value", function() {
        var model = new GraphModel({domain: [10, 30], step: 5});
        var view = new GraphView({model: model});
        assert.equal(view.snapX(12), 10);
        assert.equal(view.snapX(13), 15);
        assert.equal(view.snapX(15), 15);
        assert.equal(view.snapX(17), 15);
        assert.equal(view.snapX(18), 20);
      });
    });
  });

  describe("GraphMetricModel", function() {
    var GraphMetricModel = diamondash.widgets.graph.GraphMetricModel,
        GraphMetricCollection = diamondash.widgets.graph.GraphMetricCollection;

    var model,
        collection;

    beforeEach(function() {
      collection = new GraphMetricCollection();

      model = new GraphMetricModel(
        {datapoints: [{x: 0, y: 1}, {x: 1, y: 2}, {x: 3, y: 5}]},
        {collection: collection});
    });

    describe(".getLValue()", function() {
      it("should return the last value.", function() {
        assert.equal(model.getLValue(), 5);
      });

      it("should return null for empty datapoints.", function() {
        model.set('datapoints', []);
        assert.equal(model.getLValue(), null);
      });

      it("should return null on undefined y values.", function() {
        model.set('datapoints', [{x: 0}]);
        assert.equal(model.getLValue(), null);
      });
    });

    describe(".getValueAt()", function() {
      it("should return a value if it exists at x", function() {
        assert.equal(model.getValueAt(1), 2);
      });

      it("should return null if no value exists at x", function() {
        assert.equal(model.getValueAt(2), null);
      });

      it("should return null for empty datapoints", function() {
        model.set('datapoints', []);
        assert.equal(model.getValueAt(2), null);
      });
    });
  });
});
