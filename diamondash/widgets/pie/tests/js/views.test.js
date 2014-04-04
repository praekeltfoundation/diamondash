describe("diamondash.widgets.pie", function() {
  describe("PieView", function() {
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
