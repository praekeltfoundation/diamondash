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
        el: $('<div>')
          .width(960)
          .height(64),
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
        hover.inverse(graph, {x: 1340876295000});
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

        hover.inverse(graph, {x: 1340876295000});

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
        hover.inverse(graph, {x: 1340876295000});
        assert(legend.$el.hasClass('hover'));

        graph.trigger('unhover');
        assert(!legend.$el.hasClass('hover'));
      });

      it("should display the last metric values", function() {
        hover.inverse(graph, {x: 1340876295000});

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

  describe("GraphHoverMarker", function() {
    var marker,
        graph;

    function markerOpacities() {
      var opacities = {};

      graph.axis.line
        .selectAll('g')
        .each(function(tick) {
          if (tick) {
            opacities[tick] = $(this).css('fill-opacity');
          }
        });

      return opacities;
    }

    beforeEach(function() {
      graph = new views.GraphView({
        el: $('<div>')
          .width(960)
          .height(64),
        model: new models.GraphModel(
          fixtures.get('diamondash.widgets.graph.models.GraphModel:simple'))
      });

      marker = graph.hoverMarker;
    });

    describe("when the graph is hovered over", function() {
      beforeEach(function() {
        graph.render();
      });

      it("should show the marker", function() {
        assert.equal(graph.$('.hover-marker').length, 0);

        hover.inverse(graph, {x: 1340876295000});

        assert.equal(graph.$('.hover-marker').length, 1);
        assert.equal(graph.$('.hover-marker').text(), '28-06 09:38');
      });

      it("should hide nearby axis markers", function() {
        assert.deepEqual(markerOpacities(), {
          1340875995000: '',
          1340876295000: '',
          1340876595000: '',
          1340876895000: '',
          1340877195000: '',
          1340877495000: ''
        });

        hover.inverse(graph, {x: 1340876295000});

        assert.deepEqual(markerOpacities(), {
          1340875995000: '1',
          1340876295000: '0',
          1340876595000: '1',
          1340876895000: '1',
          1340877195000: '1',
          1340877495000: '1'
        });
      });
    });

    describe("when the graph is unhovered", function() {
      beforeEach(function() {
        graph.render();
        hover.inverse(graph, {x: 1340876295000});
      });

      it("should hide the marker", function() {
        assert.equal(graph.$('.hover-marker').length, 1);
        graph.trigger('unhover');
        assert.equal(graph.$('.hover-marker').length, 0);
      });

      it("should unhide all axis markers", function() {
        assert.deepEqual(markerOpacities(), {
          1340875995000: '1',
          1340876295000: '0',
          1340876595000: '1',
          1340876895000: '1',
          1340877195000: '1',
          1340877495000: '1'
        });

        graph.trigger('unhover');

        assert.deepEqual(markerOpacities(), {
          1340875995000: '1',
          1340876295000: '1',
          1340876595000: '1',
          1340876895000: '1',
          1340877195000: '1',
          1340877495000: '1'
        });
      });
    });
  });
});
