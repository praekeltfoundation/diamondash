describe("diamondash.widgets.graph", function() {
  var utils = diamondash.test.utils,
      fixtures = diamondash.test.fixtures,
      views = diamondash.widgets.graph.views,
      models = diamondash.widgets.graph.models;

  function hover(graph, coords) {
    coords = _(coords || {}).defaults({x: 0, y: 0});
    graph.trigger('hover', graph.positionOf(coords));
  }

  hover.inverse = function(graph, coords) {
    coords = _(coords || {}).defaults({x: 0, y: 0});

    this(graph, {
      x: graph.fx(coords.x),
      y: graph.fy(coords.y)
    });
  };

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

      legend = graph.legend;
    });

    describe("when the graph is hovered over", function() {
      beforeEach(function() {
        legend.render();
      });

      it("should add a 'hover' class to the legend", function() {
        assert(!legend.$el.hasClass('hover'));
        hover.inverse(graph, {x: 15});
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

        hover.inverse(graph, {x: 15});

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
        hover.inverse(graph, {x: 15});
        assert(legend.$el.hasClass('hover'));

        graph.trigger('unhover');
        assert(!legend.$el.hasClass('hover'));
      });

      it("should display the last metric values", function() {
        hover.inverse(graph, {x: 15});

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
});
