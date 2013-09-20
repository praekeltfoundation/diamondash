describe("diamondash.widgets.graph", function() {
  var utils = diamondash.utils,
      testUtils = diamondash.test.utils,
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
    testUtils.unregisterModels();
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

  describe("GraphDots", function() {
    var dots,
        graph;

    function dotToCoords() {
      var el = d3.select(this);

      return {
        x: graph.fx.invert(el.attr('cx')).valueOf(),
        y: Math.floor(graph.fy.invert(el.attr('cy')))
      };
    }

    function metricDotCoords(name) {
      var selection = graph.svg
        .select('.metric-dots[data-metric=' + name + ']')
        .selectAll('.dot');

      return utils.d3Map(selection, dotToCoords);
    }

    beforeEach(function() {
      graph = new views.GraphView({
        dotted: true,
        el: $('<div>')
          .width(960)
          .height(64),
        model: new models.GraphModel(
          fixtures.get('diamondash.widgets.graph.models.GraphModel:simple'))
      });

      dots = graph.dots;
    });

    describe(".render()", function() {
      it("should display the dots for each metric's datapoints", function() {
        var metrics = graph.model.get('metrics');

        assert.equal(graph.$('.metric-dots').length, 0);
        dots.render();
        assert.equal(graph.$('.metric-dots').length, 2);

        assert.deepEqual(
          metrics.get('foo').get('datapoints'),
          metricDotCoords('foo'));

        assert.deepEqual(
          metrics.get('bar').get('datapoints'),
          metricDotCoords('bar'));
      });
    });

    describe("when the graph is hovered over", function() {
      beforeEach(function() {
        graph.render();
      });
      
      it("should display dots at the hovered over location", function() {
        assert.equal(graph.$('.hover-dot').length, 0);
        hover.inverse(graph, {x: 1340876295000});
        assert.equal(graph.$('.hover-dot').length, 2);

        assert.deepEqual(
          utils.d3Map(graph.svg.selectAll('.hover-dot'), dotToCoords),
          [{x: 1340876295000, y: 12},
           {x: 1340876295000, y: 22}]);
      });
    });

    describe("when the graph is unhovered", function() {
      beforeEach(function() {
        graph.render();
        hover.inverse(graph, {x: 1340876295000});
      });

      it("should not display any hover dots", function() {
        assert.equal(graph.$('.hover-dot').length, 2);
        graph.trigger('unhover');
        assert.equal(graph.$('.hover-dot').length, 0);
      });
    });
  });

  describe("GraphLines", function() {
    var lines,
        graph;

    beforeEach(function() {
      graph = new views.GraphView({
        dotted: true,
        el: $('<div>')
          .width(960)
          .height(64),
        model: new models.GraphModel(
          fixtures.get('diamondash.widgets.graph.models.GraphModel:simple'))
      });

      lines = graph.lines;
    });

    describe(".render()", function() {
      it("should draw a line for each metric", function() {
        var metrics = graph.model.get('metrics');

        assert.equal(graph.$('.metric-line').length, 0);
        lines.render();
        assert.equal(graph.$('.metric-line').length, 2);

        assert.strictEqual(
          graph.svg
            .select('.metric-line[data-metric=foo]')
            .datum(),
          metrics.get('foo'));

        assert.strictEqual(
          graph.svg
            .select('.metric-line[data-metric=bar]')
            .datum(),
          metrics.get('bar'));
      });

      it("should color the lines according to the metrics' colors",
      function() {
        var metrics = graph.model.get('metrics');
        lines.render();

        assert.equal(
          graph
            .$('.metric-line[data-metric=foo]')
            .css('stroke'),
          metrics
            .get('foo')
            .get('color'));

        assert.equal(
          graph
            .$('.metric-line[data-metric=bar]')
            .css('stroke'),
          metrics
            .get('bar')
            .get('color'));
      });
    });
  });
});
