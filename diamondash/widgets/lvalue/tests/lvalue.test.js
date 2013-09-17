describe("diamondash.widgets.lvalue", function(){
  var utils = diamondash.test.utils;

  afterEach(function() {
    utils.unregisterModels();
  });

  describe("LValueView", function(){
    var LValueView = diamondash.widgets.lvalue.LValueView,
        LValueModel = diamondash.widgets.lvalue.LValueModel;

    var model,
        view;

    beforeEach(function() {
      model = new LValueModel({
        'name': 'some-lvalue-widget',
        'last': 9227465.0,
        'prev': 5702887.0,
        'from': 1340875995000,
        'to': 1340875995000 + 3600000 - 1,
      });

      view = new LValueView({
        model: model,
        el: $('<div>').append(
          $('<div>').addClass('widget-container'))
      });

      view.last.fadeDuration = 0;
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
        assert.equal(view.$('.last').text(), "9,227,465");

        assert(view.$('.last').hasClass('long'));
        assert(!view.$('.last').hasClass('short'));
      });
    });

    describe("when it is no longer hovered over", function() {
      beforeEach(function() {
        view.render();
        view.$el.mouseenter();
      });

      it("should display the short format of the last value", function() {
        view.$el.mouseleave();
        assert.equal(view.$('.last').text(), "9.2M");

        assert(view.$('.last').hasClass('short'));
        assert(!view.$('.last').hasClass('long'));
      });
    });

    describe(".render()", function() {
      it("should display the appropriate values", function() {
        view.render();
        assert.equal(view.$('.last').text(), "9.2M");
        assert.equal(view.$('.diff').text(), "+3.52M");
        assert.equal(view.$('.percentage').text(), "(61.80%)");
        assert.equal(view.$('.from').text(), "from 28-06-2012 09:33");
        assert.equal(view.$('.to').text(), "to 28-06-2012 10:33");
      });

      it("should set the appropriate classes on the change sub-element", function() {
        model.set({last: 2, prev: 1});
        view.render();
        assert(view.$('.change').hasClass('good'));
        assert(!view.$('.change').hasClass('bad'));
        assert(!view.$('.change').hasClass('no'));

        model.set({last: 1, prev: 2});
        view.render();
        assert(view.$('.change').hasClass('bad'));
        assert(!view.$('.change').hasClass('good'));
        assert(!view.$('.change').hasClass('no'));

        model.set({last: 1, prev: 1});
        view.render();
        assert(view.$('.change').hasClass('no'));
        assert(!view.$('.change').hasClass('good'));
        assert(!view.$('.change').hasClass('bad'));
      });
    });
  });
});
