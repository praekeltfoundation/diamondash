describe("diamondash.widgets.chart.views", function() {
  var utils = diamondash.test.utils,
      testUtils = diamondash.test.utils,
      fixtures = diamondash.test.fixtures,
      models = diamondash.widgets.chart.models,
      views = diamondash.widgets.chart.views;

  afterEach(function() {
    utils.unregisterModels();
  });

  describe(".ChartDimensions", function() {
    var dims;

    beforeEach(function() {
      dims = new views.ChartDimensions({
        height: 128,
        width: 64
      });
    });

    it("should expose its width", function() {
      assert.equal(dims.width(), 64);
    });

    it("should expose its height", function() {
      assert.equal(dims.height(), 128);
    });

    it("should expose its offset", function() {
      assert.deepEqual(dims.offset(), {
        x: 0,
        y: 0
      });
    });
  });

  describe("XYChartHoverMarker", function() {
    var marker,
    chart;

    function markerOpacities() {
      var opacities = {};

      chart.axis.line
      .selectAll('g')
      .each(function(tick) {
        if (tick) {
          opacities[tick] = $(this).css('fill-opacity');
        }
      });

      return opacities;
    }

    beforeEach(function() {
      chart = new views.XYChartView({
        el: $('<div>')
        .width(960)
        .height(64),
        model: new models.ChartModel(
          fixtures.get('diamondash.widgets.chart.models.ChartModel:simple'))
      });

      marker = chart.hoverMarker;
    });

    describe("when the chart is hovered over", function() {
      beforeEach(function() {
        chart.render();
      });

      it("should show the marker", function() {
        assert.equal(chart.$('.hover-marker').length, 0);

        testUtils.hover_axes(chart, {x: 1340876295000});

        assert.equal(chart.$('.hover-marker').length, 1);
        assert.equal(chart.$('.hover-marker').text(), '28-06 09:38');
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

        testUtils.hover_axes(chart, {x: 1340876295000});

        assert.deepEqual(markerOpacities(), {
          1340875995000: '1',
          1340876295000: '0',
          1340876595000: '1',
          1340876895000: '1',
          1340877195000: '1',
          1340877495000: '1'
        });
      });

      it("shouldn't show the hover marker if the chart has no datapoints",
      function() {
        chart.model.get('metrics').each(function(m) {
          m.set('datapoints', []);
        });

        testUtils.hover_svg(chart);

        assert.equal(chart.$('.hover-marker').length, 0);
      });
    });

    describe("when the chart is unhovered", function() {
      beforeEach(function() {
        chart.render();
        testUtils.hover_axes(chart, {x: 1340876295000});
      });

      it("should hide the marker", function() {
        assert.equal(chart.$('.hover-marker').length, 1);
        chart.trigger('unhover');
        assert.equal(chart.$('.hover-marker').length, 0);
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

        chart.trigger('unhover');

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

  describe(".ChartAxisView", function() {
    var axis,
        chart;

    beforeEach(function() {
      chart = new views.ChartView({
        model: new models.ChartModel({id: 'chart-1'}),
        dims: new views.ChartDimensions({
          width: 128,
          height: 74
        })
      });

      axis = new views.ChartAxisView({
        chart: chart,
        tickCount: 6,
        scale: d3.time.scale().range([0, chart.dims.width()])
      });
    });

    describe(".tickValues()", function() {
      it("should generate the correct tick values", function() {
        assert.deepEqual(
          axis.tickValues(2, 96, 5),
          [2, 17, 32, 47, 62, 77, 92, 96]);

        assert.deepEqual(
          axis.tickValues(3, 98, 5),
          [3, 18, 33, 48, 63, 78, 93, 98]);
      });
    });

    describe(".render()", function() {
      it("should display the correct tick values", function() {
        axis.render(
          1340875995000,
          1340875995000 + (60 * 60 * 1000),
          5 * 1000 * 60);

        assert.equal(
          axis.line.text(),
          ['28-06 09:33',
           '28-06 09:43',
           '28-06 09:53',
           '28-06 10:03',
           '28-06 10:13',
           '28-06 10:23',
           '28-06 10:33'].join(''));
      });
    });
  });

  describe(".ChartView", function() {
    var  chart;

    beforeEach(function() {
      chart = new views.ChartView({
        model: new models.ChartModel({id: 'chart-1'}),
        dims: new views.ChartDimensions({
          width: 128,
          height: 74,
          margin: {
            left: 2,
            right: 2,
            top: 2,
            bottom: 2
          }
        })
      });
    });

    describe("when its dimensions change", function() {
      it("should retranslate the chart", function() {
        assert.equal(chart.canvas.attr('transform'), 'translate(2,2)');

        chart.dims.set('offset', {
          x: 4,
          y: 4
        });

        assert.equal(chart.canvas.attr('transform'), 'translate(6,6)');
      });

      it("should resize the chart", function() {
        assert.equal(chart.svg.attr('width'), '128');
        assert.equal(chart.svg.attr('height'), '74');

        chart.dims.set({
          width: 123,
          height: 64
        });

        assert.equal(chart.svg.attr('width'), '123');
        assert.equal(chart.svg.attr('height'), '64');
      });

      it("should resize the chart's overlay's", function() {
        assert.equal(chart.overlay.attr('width'), '128');
        assert.equal(chart.overlay.attr('height'), '74');

        chart.dims.set({
          width: 123,
          height: 64
        });

        assert.equal(chart.overlay.attr('width'), '123');
        assert.equal(chart.overlay.attr('height'), '64');
      });
    });
  });

  describe("ChartLegendView", function() {
    var legend,
        chart;

    beforeEach(function() {
      chart = new views.XYChartView({
        el: $('<div>')
          .width(960)
          .height(64),
        model: new models.ChartModel(
          fixtures.get('diamondash.widgets.chart.models.ChartModel:simple')),
      });

      legend = new views.ChartLegendView({chart: chart});
      chart.render();
      legend.render();
    });

    describe("if the chart metrics have no datapoints", function() {
      beforeEach(function() {
        chart.model.get('metrics').each(function(m) {
          m.set('datapoints', []);
        });
      });

      it("should use the chart's default value", function() {
        chart.model.set('default_value', -1);
        legend.render();

        assert.equal(
          legend.$('.legend-item[data-metric-id=metric-a] .value').text(),
          -1);

        assert.equal(
          legend.$('.legend-item[data-metric-id=metric-b] .value').text(),
          -1);
      });
    });

    describe("when the chart is hovered over", function() {
      it("should add a 'hover' class to the legend", function() {
        assert(!legend.$el.hasClass('hover'));
        testUtils.hover_axes(chart, {x: 1340876295000});
        assert(legend.$el.hasClass('hover'));
      });

      it("should display the metric values at the hovered over time interval",
      function() {
        assert.equal(
          legend.$('.legend-item[data-metric-id=metric-a] .value').text(),
          24);

        assert.equal(
          legend.$('.legend-item[data-metric-id=metric-b] .value').text(),
          16);

        testUtils.hover_axes(chart, {x: 1340876295000});

        assert.equal(
          legend.$('.legend-item[data-metric-id=metric-a] .value').text(),
          12);

        assert.equal(
          legend.$('.legend-item[data-metric-id=metric-b] .value').text(),
          22);
      });
    });

    describe("when the chart is unhovered", function() {
      it("should remove the 'hover' class from the legend", function() {
        testUtils.hover_axes(chart, {x: 1340876295000});
        assert(legend.$el.hasClass('hover'));

        chart.trigger('unhover');
        assert(!legend.$el.hasClass('hover'));
      });

      it("should display the last metric values", function() {
        testUtils.hover_axes(chart, {x: 1340876295000});

        assert.equal(
          legend.$('.legend-item[data-metric-id=metric-a] .value').text(),
          12);

        assert.equal(
          legend.$('.legend-item[data-metric-id=metric-b] .value').text(),
          22);

        chart.trigger('unhover');

        assert.equal(
          legend.$('.legend-item[data-metric-id=metric-a] .value').text(),
          24);

        assert.equal(
          legend.$('.legend-item[data-metric-id=metric-b] .value').text(),
          16);
      });
    });
  });

  describe(".XYChartView", function() {
    var chart;

    beforeEach(function() {
      chart = new views.XYChartView({
        el: $('<div>')
          .width(960)
          .height(64),
        model: new models.ChartModel(
          fixtures.get('diamondash.widgets.chart.models.ChartModel:simple'))
      });
    });

    describe("when the mouse is moved over the chart", function() {
      beforeEach(function() {
        chart.dims.set('margin', {
          left: 0,
          right: 0,
          top: 0,
          bottom: 0
        });

        chart.render();
        sinon.stub(d3, 'mouse', _.identity);
      });

      afterEach(function() {
        d3.mouse.restore();
      });

      it("should trigger an event with the calculated position information",
      function(done) {
        chart.render();

        chart.on('hover', function(position) {
          assert.equal(position.x, 1340876295000);
          assert.equal(position.svg.x, 192);
          assert.equal(position.svg.y, -11);
          done();
        });

        chart.trigger('mousemove', [192, -11]);
      });
    });

    describe("when the mouse is moved away from the chart", function() {
      it("should trigger an event", function(done) {
        chart.on('unhover', function() { done(); });
        chart.trigger('mouseout');
      });
    });

    describe(".render", function() {
      it("should render the chart's axis", function() {
        assert.equal(chart.$('.axis').text(), '');

        chart.render();

        assert.equal(
          chart.$('.axis').text(),
          ['28-06 09:33',
            '28-06 09:38',
            '28-06 09:43',
            '28-06 09:48',
            '28-06 09:53',
            '28-06 09:58'].join(''));
      });
    });
  });
});
