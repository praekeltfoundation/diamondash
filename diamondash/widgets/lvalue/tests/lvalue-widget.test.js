var LValueWidgetView = diamondash.widgets.LValueWidgetView,
    LValueWidgetModel = diamondash.widgets.LValueWidgetModel;

describe("LValueWidgetView", function(){
  var model, view;

  beforeEach(function() {
    model = new LValueWidgetModel({
      'name': 'some-lvalue-widget',
      'lvalue': 9227465.0,
      'from': 1340875995,
      'to': 1340875995 + 3600 - 1,
      'diff': 9227465.0 - 5702887.0,
      'percentage': 0.61803398874990854
    });

    view = new LValueWidgetView({
      model: model,
      el: $([
        "<div>",
          LValueWidgetView.prototype.slotSelectors.map(function(s) {
            return "<span class=" + s.slice(1) + "></span>"; }
          ).join(''),
          "<span class='lvalue-change'></span>",
        "</div>"
      ].join(''))
    });
  });

  afterEach(function() {
    $('body').html("");
  });

  describe(".render()", function() {
    it("should apply appropriate values to the slots", function() {
      view.render();
      assert.equal(view.$('.lvalue-lvalue-slot').text(), "9.2M");
      assert.equal(view.$('.lvalue-diff-slot').text(), "3.52M");
      assert.equal(view.$('.lvalue-percentage-slot').text(), "62%");
      assert.equal(view.$('.lvalue-from-slot').text(), "28-06-2012 11:33");
      assert.equal(view.$('.lvalue-to-slot').text(), "28-06-2012 12:33");
    });

    it("should set the appropriate classes on the change div", function() {
      model.set('diff', 1);
      view.render();
      assert(view.$('.lvalue-change').hasClass('good-diff'));
      assert(!view.$('.lvalue-change').hasClass('bad-diff'));

      model.set('diff', -1);
      view.render();
      assert(!view.$('.lvalue-change').hasClass('good-diff'));
      assert(view.$('.lvalue-change').hasClass('bad-diff'));

      model.set('diff', 0);
      view.render();
      assert(!view.$('.lvalue-change').hasClass('good-diff'));
      assert(!view.$('.lvalue-change').hasClass('bad-diff'));
    });
  });
});
