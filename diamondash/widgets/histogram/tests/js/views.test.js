describe("diamondash.widgets.histogram", function() {
  var models = diamondash.widgets.histogram.models,
      views = diamondash.widgets.histogram.views,
      fixtures = diamondash.test.fixtures,
      testUtils = diamondash.test.utils;

  describe("HistogramView", function() {
    var histogram;

    function draw_histogram(opts) {
      var $svg = $('<svg>');

      var fx = d3
        .scale.linear()
        .domain(opts.model.domain())
        .range([0, opts.chartWidth]);

      var fy = d3
        .scale.linear()
        .domain(opts.model.range())
        .range([opts.chartHeight, 0]);

      var format = d3.format(".2s");

      var barWidth = fx(opts.model.get('bucket_size')) - fx(0);
      barWidth -= opts.barPadding;

      d3.select($svg.get(0))
        .selectAll('.bar')
        .data(opts.model
          .get('metrics')
          .at(0)
          .get('datapoints')
          .slice(1))
        .enter()
          .append('g')
          .attr('class', 'bar')
          .attr('transform', function(d) {
            var x = fx(d.x - opts.model.get('bucket_size'));
            return "translate(" + x + "," + fy(d.y) + ")";
          })
          .append('rect')
            .style('fill', opts.color)
            .attr("width", barWidth)
            .attr("height", function(d) {
              return opts.chartHeight - fy(d.y);
            })
          .append('text')
            .text(function(d) {
              return format(d.y);
            });

      return $svg;
    }

    beforeEach(function() {
      histogram = new views.HistogramView({
        el: $('<div>')
          .width(960)
          .height(278),
        model: new models.HistogramModel(
          fixtures.get(
            'diamondash.widgets.histogram.models.HistogramModel:simple'))
      });

      histogram.dims.set('margin', {
        left: 2,
        right: 2,
        top: 2,
        bottom: 2
      });
    });

    afterEach(function() {
      testUtils.unregisterModels();
    });
    
    describe("when the chart is hovered over", function() {
      it("should mark whether a bar is hovered", function() {
        histogram.render();

        testUtils.hover_axes(histogram, {
          x: 1340876595000 - (5 * 1000 * 60)
        });

        var $bars = histogram.$('.bar');
        assert.equal($bars.eq(0).attr('class'), 'not-hover bar');
        assert.equal($bars.eq(1).attr('class'), 'hover bar');
        assert.equal($bars.eq(2).attr('class'), 'not-hover bar');
        assert.equal($bars.eq(3).attr('class'), 'not-hover bar');
        assert.equal($bars.eq(4).attr('class'), 'not-hover bar');
      });

      it("should use a longer text format for the hovered over bar", function() {
        histogram.model.get('metrics').at(0).set('datapoints', [
          {x: 1340875995000, y: 18000000},
          {x: 1340876295000, y: 12000000},
          {x: 1340876595000, y: 6000000},
          {x: 1340877195000, y: 21000000},
          {x: 1340877495000, y: 24000000}]);

        histogram.render();

        testUtils.hover_axes(histogram, {
          x: 1340876595000 - (5 * 1000 * 60)
        });

        var $bars = histogram.$('.bar');
        assert.equal($bars.eq(1).text(), '6,000,000');
      });
    });

    describe(".render", function() {
      it("should render its bars", function() {
        histogram.render();

        $svg = draw_histogram({
          color: histogram.model.get('metrics').at(0).get('color'),
          chartWidth: 960 - 4,
          chartHeight: 278 - 24 - 4,
          barPadding: 2,
          model: histogram.model
        });

        var $actual = histogram.$('.bar');
        var $expected = $svg.find('.bar');
        assert.equal($actual.length, 5);

        _(5).times(function(i) {
          assert.equal(
            $actual.eq(i).attr('transform'), 
            $expected.eq(i).attr('transform'));

          assert.equal(
            $actual.eq(i).find('rect').attr('height'), 
            $expected.eq(i).find('rect').attr('height'));

          assert.equal(
            $actual.eq(i).find('rect').attr('width'), 
            $expected.eq(i).find('rect').attr('width'));

          assert.equal(
            $actual.eq(i).find('text').text(), 
            $expected.eq(i).find('text').text());
        });
      });

      it("should re-render its bars based on model changes", function() {
        histogram.render();
        histogram.model.get('metrics').at(0).set('datapoints', [
          {x: 1340875995000, y: 18},
          {x: 1340876295000, y: 12},
          {x: 1340876595000, y: 6},
          {x: 1340877195000, y: 21},
          {x: 1340877495000, y: 24}]);
        histogram.render();

        $svg = draw_histogram({
          color: histogram.model.get('metrics').at(0).get('color'),
          chartWidth: 960 - 4,
          chartHeight: 278 - 24 - 4,
          barPadding: 2,
          model: histogram.model
        });

        var $actual = histogram.$('.bar');
        var $expected = $svg.find('.bar');
        assert.equal($actual.length, 4);

        _(4).times(function(i) {
          assert.equal(
            $actual.eq(i).attr('transform'), 
            $expected.eq(i).attr('transform'));

          assert.equal(
            $actual.eq(i).find('rect').attr('height'), 
            $expected.eq(i).find('rect').attr('height'));

          assert.equal(
            $actual.eq(i).find('rect').attr('width'), 
            $expected.eq(i).find('rect').attr('width'));

          assert.equal(
            $actual.eq(i).find('text').text(), 
            $expected.eq(i).find('text').text());
        });
      });
    });
  });
});
