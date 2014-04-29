describe("diamondash.widgets.pie", function() {
  var models = diamondash.widgets.pie.models,
      testUtils = diamondash.test.utils,
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

    function draw_pie(opts) {
      var $svg = $('<svg>');

      var layout = d3.layout.pie().value(function(d) {
        return d.v;
      });

      d3.select($svg.get(0))
        .selectAll('.arc')
        .data(layout(opts.data), function(d) {
          return d.data.k;
        })
        .enter()
          .append('path')
          .attr('class', 'arc')
          .attr('d', d3.svg.arc()
            .outerRadius(opts.radius)
            .innerRadius(0));

      return $svg;
    }

    beforeEach(function() {
      pie = new views.PieView({
        el: $('<div>').width(960),
        model: new models.PieModel(
          fixtures.get('diamondash.widgets.pie.models.PieModel:simple'))
      });
    });
    
    afterEach(function() {
      testUtils.unregisterModels();
    });

    describe(".render", function() {
      it("should render a pie chart from its model's metrics", function() {
        assert.lengthOf(pie.$('.arc'), 0);
        pie.render();
        assert.lengthOf(pie.$('.arc'), 3);

        var $pie = draw_pie({
          radius: 960 / 2,
          data: [{
            k: 'metric-a',
            v: 18
          }, {
            k: 'metric-b',
            v: 8
          }, {
            k: 'metric-c',
            v: 34
          }]
        });

        var $actual = pie.$('.arc');
        var $expected = $pie.find('.arc');
        assert.equal($actual.eq(0).attr('d'), $expected.eq(0).attr('d'));
        assert.equal($actual.eq(1).attr('d'), $expected.eq(1).attr('d'));
        assert.equal($actual.eq(2).attr('d'), $expected.eq(2).attr('d'));

        var metrics = pie.model.get('metrics');
        assert.equal($actual.eq(0).css('fill'), metrics.at(0).get('color'));
        assert.equal($actual.eq(1).css('fill'), metrics.at(1).get('color'));
        assert.equal($actual.eq(2).css('fill'), metrics.at(2).get('color'));
      });

      it("should re-render correctly based on model changes", function() {
        pie.render();

        pie.model.get('metrics').set([{
          id: 'metric-a',
          datapoints: [{x: 1340875995000, y: 3}]
        }, {
          id: 'metric-b',
          datapoints: [{x: 1340875995000, y: 2}]
        }, {
          id: 'metric-c',
          datapoints: [{x: 1340875995000, y: 9}]
        }]);

        pie.render();

        var $pie = draw_pie({
          radius: 960 / 2,
          data: [{
            k: 'metric-a',
            v: 3
          }, {
            k: 'metric-b',
            v: 2
          }, {
            k: 'metric-c',
            v: 9
          }]
        });

        var $actual = pie.$('.arc');
        var $expected = $pie.find('.arc');

        assert.equal($actual.eq(0).attr('d'), $expected.eq(0).attr('d'));
        assert.equal($actual.eq(1).attr('d'), $expected.eq(1).attr('d'));
        assert.equal($actual.eq(2).attr('d'), $expected.eq(2).attr('d'));
      });
    });
  });
});
