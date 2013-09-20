describe("diamondash.widgets.graph", function() {
  var utils = diamondash.test.utils,
      fixtures = diamondash.test.fixtures,
      views = diamondash.widgets.graph.views,
      models = diamondash.widgets.graph.models;

  afterEach(function() {
    utils.unregisterModels();
  });

  describe("GraphLegendView", function() {
    var legend,
        graph;

    beforeEach(function() {
      graph = new views.GraphView({
        model: new models.GraphModel(
          fixtures.get('diamondash.widgets.graph.models.GraphModel:simple'))
      });

      legend = new views.GraphLegendView({graph: graph});
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
  });
});
