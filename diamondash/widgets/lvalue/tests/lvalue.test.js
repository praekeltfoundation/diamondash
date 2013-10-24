describe("diamondash.widgets.lvalue", function(){
  var utils = diamondash.test.utils,
      lvalue = diamondash.widgets.lvalue;

  afterEach(function() {
    utils.unregisterModels();
  });

  describe("LValueModel", function(){
    var model;

    beforeEach(function() {
      model = new lvalue.LValueModel({
        'name': 'some-lvalue-widget',
        'last': 9227465.0,
        'prev': 5702887.0,
        'from': 1340875995000,
        'to': 1340875995000 + 3600000 - 1,
      });
    });

    describe(".validate", function() {
      it("should validate its 'last' attr", function() {
        assert(model.isValid());
        model.unset('last');
        assert(!model.isValid());
        assert.equal(
          model.validationError,
          "LValueModel has bad 'last' attr: undefined");

        model.set('last', null);
        assert(!model.isValid());
        assert.equal(
          model.validationError,
          "LValueModel has bad 'last' attr: null");

        model.set('last', 0);
        assert(model.isValid());
      });

      it("should validate its 'prev' attr", function() {
        assert(model.isValid());
        model.unset('prev');
        assert(!model.isValid());
        assert.equal(
          model.validationError,
          "LValueModel has bad 'prev' attr: undefined");

        model.set('prev', null);
        assert(!model.isValid());
        assert.equal(
          model.validationError,
          "LValueModel has bad 'prev' attr: null");

        model.set('prev', 0);
        assert(model.isValid());
      });

      it("should validate its 'from' attr", function() {
        assert(model.isValid());
        model.unset('from');
        assert(!model.isValid());
        assert.equal(
          model.validationError,
          "LValueModel has bad 'from' attr: undefined");

        model.set('from', null);
        assert(!model.isValid());
        assert.equal(
          model.validationError,
          "LValueModel has bad 'from' attr: null");

        model.set('from', 0);
        assert(model.isValid());
      });

      it("should validate its 'to' attr", function() {
        assert(model.isValid());
        model.unset('to');
        assert(!model.isValid());
        assert.equal(
          model.validationError,
          "LValueModel has bad 'to' attr: undefined");

        model.set('to', null);
        assert(!model.isValid());
        assert.equal(
          model.validationError,
          "LValueModel has bad 'to' attr: null");

        model.set('to', 0);
        assert(model.isValid());
      });
    });
  });

  describe("LValueView", function(){
    var model,
        view;

    beforeEach(function() {
      model = new lvalue.LValueModel({
        'name': 'some-lvalue-widget',
        'last': 9227465.0,
        'prev': 5702887.0,
        'from': 1340875995000,
        'to': 1340875995000 + 3600000 - 1,
      });

      view = new lvalue.LValueView({
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
      it("should not change its contents if the model is invalid", function() {
        view.render();

        var contents = view.$el.html();
        assert(contents);

        model.unset('last');
        view.render();
        assert.equal(view.$el.html(), contents);
      });

      it("should display the appropriate values", function() {
        view.render();
        assert.include(view.$('.last').text(), "9.2M");
        assert.include(view.$('.diff').text(), "+3.52M");
        assert.include(view.$('.percentage').text(), "(61.80%)");
        assert.include(view.$('.from').text(), "from 28-06-2012 09:33");
        assert.include(view.$('.to').text(), "to 28-06-2012 10:33");
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
