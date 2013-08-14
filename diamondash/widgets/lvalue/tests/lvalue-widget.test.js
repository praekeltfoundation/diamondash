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

    view = new LValueWidgetView({
      model: model,
      el: $('<div>').append(
        $('<div>').addClass('widget-container'))
    });

    view.value.fadeDuration = 0;
  });

  afterEach(function() {
    view.remove();
  });

  describe("when it is hovered over", function() {
    beforeEach(function() {
      view.render();
    });

    it("should display the long format of the last value", function() {
      view.$el.mouseenter();
      assert.equal(view.$('.value').text(), "9,227,465");

      assert(view.$('.value').hasClass('long'));
      assert(!view.$('.value').hasClass('short'));
    });
  });

  describe("when it is no longer hovered over", function() {
    beforeEach(function() {
      view.render();
      view.$el.mouseenter();
    });

    it("should display the short format of the last value", function() {
      view.$el.mouseleave();
      assert.equal(view.$('.value').text(), "9.2M");

      assert(view.$('.value').hasClass('short'));
      assert(!view.$('.value').hasClass('long'));
    });
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
      assert(view.$('.change').hasClass('good'));
      assert(!view.$('.change').hasClass('bad'));
      assert(!view.$('.change').hasClass('no'));

      model.set('diff', -1);
      view.render();
      assert(view.$('.change').hasClass('bad'));
      assert(!view.$('.change').hasClass('good'));
      assert(!view.$('.change').hasClass('no'));

      model.set('diff', 0);
      view.render();
      assert(view.$('.change').hasClass('no'));
      assert(!view.$('.change').hasClass('good'));
      assert(!view.$('.change').hasClass('bad'));
    });
  });
});
