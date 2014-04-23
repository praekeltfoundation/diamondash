describe("diamondash.widgets.pie", function() {
  var models = diamondash.widgets.pie.models,
      views = diamondash.widgets.pie.views;

  describe(".PieDimensions", function() {
    var dims;

    beforeEach(function() {
      dims = new views.PieDimensions({
        width: 64,
        scale: 0.4,
        margin: {
          top: 2,
          right: 2,
          bottom: 2,
          left: 2
        }
      });
    });

    it("should expose its scale", function() {
        assert.equal(dims.scale(), 0.4);
    });

    it("should expose its height", function() {
        assert.equal(dims.height(), 64 * 0.4);
    });

    it("should expose its radius", function() {
        assert.equal(dims.radius(), (64 / 2) * 0.4);
    });

    it("should expose its offset", function() {
        assert.deepEqual(dims.offset(), {
            x: 64 / 2,
            y: (64 / 2) * 0.4
        });
    });
  });

  describe(".PieView", function() {
    var pie;

    beforeEach(function() {
      pie = new views.PieView({
        el: $('<div>')
          .width(960)
          .height(64),
        model: new models.PieModel(
          fixtures.get('diamondash.widgets.pie.models.PieModel:simple'))
      });
    });
  });
});
