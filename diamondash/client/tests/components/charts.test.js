describe("diamondash.components.charts", function() {
  var charts = diamondash.components.charts;

  describe(".Dimensions", function() {
    var dimensions;

    beforeEach(function() {
      dimensions = new charts.Dimensions({
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

    it("should calculate the inner dimensions", function() {
      assert.equal(dimensions.innerWidth, 60);
      assert.equal(dimensions.innerHeight, 124);
    });
  });

  describe(".AxisView", function() {
    var axis,
        chart;

    beforeEach(function() {
      chart = new charts.ChartView({
        dimensions: new charts.Dimensions({
          width: 128,
          height: 74
        })
      });

      axis = new charts.AxisView({
        chart: chart,
        tickCount: 6,
        scale: d3.time.scale().range([0, chart.dimensions.innerWidth])
      });
    });

    describe(".tickValues()", function() {
      it("should generate the correct tick values", function() {
        assert.deepEqual(
          axis.tickValues(2, 96, 5),
          d3.range(2, 96, 5 * 3));

        assert.deepEqual(
          axis.tickValues(3, 98, 5),
          d3.range(3, 98, 5 * 3));
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
           '28-06 10:23'].join(''));
      });
    });
  });
});
