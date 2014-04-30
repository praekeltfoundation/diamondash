describe("diamondash.widgets.graph", function() {
  var utils = diamondash.utils,
      testUtils = diamondash.test.utils,
      fixtures = diamondash.test.fixtures,
      views = diamondash.widgets.graph.views,
      models = diamondash.widgets.graph.models;

  afterEach(function() {
    testUtils.unregisterModels();
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

        testUtils.hover_axes(graph, {x: 1340876295000});

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

        testUtils.hover_axes(graph, {x: 1340876295000});

        assert.deepEqual(markerOpacities(), {
          1340875995000: '1',
          1340876295000: '0',
          1340876595000: '1',
          1340876895000: '1',
          1340877195000: '1',
          1340877495000: '1'
        });
      });

      it("shouldn't show the hover marker if the graph has no datapoints",
      function() {
        graph.model.get('metrics').each(function(m) {
          m.set('datapoints', []);
        });

        testUtils.hover_svg(graph);

        assert.equal(graph.$('.hover-marker').length, 0);
      });
    });

    describe("when the graph is unhovered", function() {
      beforeEach(function() {
        graph.render();
        testUtils.hover_axes(graph, {x: 1340876295000});
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

    function metricDotCoords(id) {
      var selection = graph.svg
      .select('.metric-dots[data-metric-id=' + id + ']')
      .selectAll('.dot');

      return utils.d3Map(selection, dotToCoords);
    }

    beforeEach(function() {
      graph = new views.GraphView({
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
          metrics.get('metric-a').get('datapoints'),
          metricDotCoords('metric-a'));

        assert.deepEqual(
          metrics.get('metric-b').get('datapoints'),
          metricDotCoords('metric-b'));
      });
    });

    describe("when the graph is hovered over", function() {
      beforeEach(function() {
        graph.render();
      });

      it("should display dots at the hovered over location", function() {
        assert.equal(graph.$('.hover-dot').length, 0);
        testUtils.hover_axes(graph, {x: 1340876295000});
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
        testUtils.hover_axes(graph, {x: 1340876295000});
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
            .select('.metric-line[data-metric-id=metric-a]')
            .datum(),
          metrics.get('metric-a'));

        assert.strictEqual(
          graph.svg
            .select('.metric-line[data-metric-id=metric-b]')
            .datum(),
          metrics.get('metric-b'));
      });

      it("should color the lines according to the metrics' colors",
      function() {
         var metrics = graph.model.get('metrics');
         lines.render();

         assert.equal(
           graph
             .$('.metric-line[data-metric-id=metric-a]')
             .css('stroke'),

         metrics
           .get('metric-a')
           .get('color'));

         assert.equal(
           graph
             .$('.metric-line[data-metric-id=metric-b]')
             .css('stroke'),
           metrics
             .get('metric-b')
             .get('color'));
      });
    });
  });

  describe("GraphLines", function() {
    var graph;

    function domain() {
      return graph.fx
      .domain()
      .map(function(d) { return d.valueOf(); });
    }

    function range() {
      return graph.fy.domain();
    }

    beforeEach(function() {
      graph = new views.GraphView({
        el: $('<div>')
        .width(960)
        .height(64),
        model: new models.GraphModel(
          fixtures.get('diamondash.widgets.graph.models.GraphModel:simple'))
      });
    });

    describe(".render()", function() {
      it("should refresh the graph domain and range", function() {
        graph.render();

        assert.deepEqual(
          domain(),
          [1340875995000, 1340877495000]);

        assert.deepEqual(
          range(),
          [2, 24]);

        graph.model.get('metrics').set([{
          id: 'metric-a',
          datapoints: [{
            x: 1340875998000,
            y: 3
          }, {
            x: 1340877498000,
            y: 25
          }]
        }]);

        graph.render();

        assert.deepEqual(
          domain(),
          [1340875998000, 1340877498000]);

        assert.deepEqual(
          range(),
          [3, 25]);
      });

      it("draw render its lines", function() {
        assert.equal(graph.$('.metric-line').length, 0);
        graph.render();
        assert.equal(graph.$('.metric-line').length, 2);
      });

      it("draw render its legend", function() {
        assert.equal(graph.$('.legend').length, 0);
        graph.render();
        assert.equal(graph.$('.legend').length, 1);
      });

      it("should draw its axis", function() {
        assert.equal(graph.$('.axis').text(), '');

        graph.render();

        assert.equal(
          graph.$('.axis').text(),
          ['28-06 09:33',
            '28-06 09:38',
            '28-06 09:43',
            '28-06 09:48',
            '28-06 09:53',
            '28-06 09:58'].join(''));
      });

      describe("if the graph is dotted", function() {
        beforeEach(function() {
          graph.model.set('dotted', true);
        });

        it("should draw its dots", function() {
          assert.equal(graph.$('.metric-dots').length, 0);
          graph.render();
          assert.equal(graph.$('.metric-dots').length, 2);
        });
      });
    });
  });
});
