describe("diamondash.widgets.graph", function() {
  var utils = diamondash.test.utils,
      fixtures = diamondash.test.fixtures;

  afterEach(function() {
    utils.unregisterModels();
  });

  describe("GraphLegendView", function() {
    var GraphModel = diamondash.widgets.graph.GraphModel,
        GraphView = diamondash.widgets.graph.GraphView,
        GraphLegendView = diamondash.widgets.graph.GraphLegendView;

    var legend,
        graph;

    beforeEach(function() {
      graph = new GraphView({
        model: new GraphModel(fixtures.get('diamondash.widgets.graph:simple'))
      });

      legend = new GraphLegendView({graph: graph});
    });

    describe("when the graph is hovered over", function() {
      beforeEach(function() {
        legend.render();
      });

      it("should add a 'hover' class to the legend", function() {
        assert(!legend.$el.hasClass('hover'));
        graph.trigger('hover', 15);
        assert(legend.$el.hasClass('hover'));
      });

      it("should display the metric values at the hovered over time interval",
      function() {
        assert.equal(
          legend.$('.legend-item[data-name="foo"] .value').text(),
          24);

        assert.equal(
          legend.$('.legend-item[data-name="bar"] .value').text(),
          16);

        graph.trigger('hover', 15);

        assert.equal(
          legend.$('.legend-item[data-name="foo"] .value').text(),
          12);

        assert.equal(
          legend.$('.legend-item[data-name="bar"] .value').text(),
          22);
      });
    });

    describe("when the graph is unhovered", function() {
      beforeEach(function() {
        legend.render();
      });

      it("should remove the 'hover' class from the legend", function() {
        graph.trigger('hover', 15);
        assert(legend.$el.hasClass('hover'));

        graph.trigger('unhover');
        assert(!legend.$el.hasClass('hover'));
      });

      it("should display the last metric values", function() {
        graph.trigger('hover', 15);

        assert.equal(
          legend.$('.legend-item[data-name="foo"] .value').text(),
          12);

        assert.equal(
          legend.$('.legend-item[data-name="bar"] .value').text(),
          22);

        graph.trigger('unhover');

        assert.equal(
          legend.$('.legend-item[data-name="foo"] .value').text(),
          24);

        assert.equal(
          legend.$('.legend-item[data-name="bar"] .value').text(),
          16);
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
    var GraphMetricModel = diamondash.widgets.graph.GraphMetricModel;

    var model;

    beforeEach(function() {
      model = new GraphMetricModel({
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
    var GraphMetricCollection = diamondash.widgets.graph.GraphMetricCollection;

    var collection;

    beforeEach(function() {
      collection = new GraphMetricCollection();
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
