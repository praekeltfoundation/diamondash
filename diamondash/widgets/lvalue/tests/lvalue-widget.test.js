var LValueWidgetView = diamondash.widgets.LValueWidgetView,
    LValueWidgetModel = diamondash.widgets.LValueWidgetModel;

describe("LValueWidgetView", function(){
  var model,
      view;

  beforeEach(function() {
    model = new LValueWidgetModel({
      'name': 'some-lvalue-widget',
      'lvalue': 9227465.0,
      'from': 1340875995000,
      'to': 1340875995000 + 3600000 - 1,
      'diff': 9227465.0 - 5702887.0,
      'percentage': 0.61803398874990854
    });

    view = new LValueWidgetView({model: model});
  });

  describe(".render()", function() {
    it("should display the appropriate values", function() {
      view.render();
      assert.equal(view.$('.value').text(), "9.2M");
      assert.equal(view.$('.diff').text(), "+3.52M");
      assert.equal(view.$('.percentage').text(), "61.80%");
      assert.equal(view.$('.from').text(), "from 28-06-2012 09:33");
      assert.equal(view.$('.to').text(), "to 28-06-2012 10:33");
    });

    it("should set the appropriate classes on the change sub-element", function() {
      model.set('diff', 1);
      view.render();
      assert(view.$('.good.change').length);
      assert(!view.$('.bad.change').length);
      assert(!view.$('.no.change').length);

      model.set('diff', -1);
      view.render();
      assert(view.$('.bad.change').length);
      assert(!view.$('.good.change').length);
      assert(!view.$('.no.change').length);

      model.set('diff', 0);
      view.render();
      assert(view.$('.no.change').length);
      assert(!view.$('.good.change').length);
      assert(!view.$('.bad.change').length);
    });
  });
});
