describe("diamondash.widgets.chart.views", function() {
  var utils = diamondash.test.utils,
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
        width: 64,
        margin: {
          top: 2,
          right: 2,
          bottom: 2,
          left: 2
        }
      });
    });

    it("should expose its width", function() {
      assert.equal(dims.width(), 64);
    });

    it("should expose its height", function() {
      assert.equal(dims.height(), 128);
    });

    it("should expose its margin", function() {
      assert.deepEqual(dims.margin(), {
        top: 2,
        right: 2,
        bottom: 2,
        left: 2
      });
    });

    it("should expose its inner width", function() {
      assert.equal(dims.innerWidth(), 60);
    });

    it("should expose its inner height", function() {
      assert.equal(dims.innerHeight(), 124);
    });

    it("should expose its offset", function() {
      assert.deepEqual(dims.offset(), {
        x: 2,
        y: 2
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
        scale: d3.time.scale().range([0, chart.dims.innerWidth()])
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
            top: 2,
            right: 2,
            bottom: 2,
            left: 2
          }
        })
      });
    });

    describe("when its dimensions change", function() {
      it("should retranslate the chart", function() {
        assert.equal(chart.canvas.attr('transform'), 'translate(2,2)');

        chart.dims.set('margin', {
          top: 4,
          right: 2,
          bottom: 2,
          left: 4
        });

        assert.equal(chart.canvas.attr('transform'), 'translate(4,4)');
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
});
