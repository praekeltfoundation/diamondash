describe("diamondash.widgets.pie", function() {
  var models = diamondash.widgets.pie.models,
      views = diamondash.widgets.pie.views,
      fixtures = diamondash.test.fixtures;

  describe(".PieDimensions", function() {
    var dims;

    beforeEach(function() {
      dims = new views.PieDimensions({width: 64});
    });

    it("should expose its width as its height", function() {
        assert.equal(dims.height(), 64);
    });

    it("should expose its radius", function() {
        assert.equal(dims.radius(), 64 / 2);
    });

    it("should expose its offset", function() {
        assert.deepEqual(dims.offset(), {
            x: 64 / 2,
            y: 64 / 2
        });
    });
  });

  describe(".PieView", function() {
    var pie;

    beforeEach(function() {
      pie = new views.PieView({
        el: $('<div>').width(960),
        model: new models.PieModel(
          fixtures.get('diamondash.widgets.pie.models.PieModel:simple'))
      });
    });

    describe(".render", function() {
      it("should render a pie chart from its model's metrics", function() {
        assert.lengthOf(pie.$('.arc'), 0);
        pie.render();
        assert.lengthOf(pie.$('.arc'), 3);

        var $svg = $('<svg>');
        d3.select($svg.get(0))
          .selectAll('.arc')
          .data(d3.layout.pie()([18, 8, 34]))
          .enter()
            .append('g')
            .attr('class', 'arc')
              .append('path')
              .attr('d', d3.svg.arc()
                .outerRadius(960 / 2)
                .innerRadius(0));

        var $actual = pie.$('.arc path');
        var $expected = $svg.find('.arc path');
        assert.equal($actual.eq(0).attr('d'), $expected.eq(0).attr('d'));
        assert.equal($actual.eq(1).attr('d'), $expected.eq(1).attr('d'));
        assert.equal($actual.eq(2).attr('d'), $expected.eq(2).attr('d'));

        var metrics = pie.model.get('metrics');
        assert.equal($actual.eq(0).css('fill'), metrics.at(0).get('color'));
        assert.equal($actual.eq(1).css('fill'), metrics.at(1).get('color'));
        assert.equal($actual.eq(2).css('fill'), metrics.at(2).get('color'));
      });
    });
  });
});
