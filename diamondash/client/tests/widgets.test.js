describe("diamondash.widgets", function(){
  var widgets = diamondash.widgets,
      widget = diamondash.widgets.widget;

  var ToyWidgetView = Backbone.View.extend();

  describe(".WidgetViewSet", function() {
    var views;

    beforeEach(function() {
      views = new widgets.WidgetViewSet();
      widgets.registry.views.add('toy', ToyWidgetView);
    });

    afterEach(function() {
      widgets.registry.views.remove('toy');
    });

    describe(".make", function() {
      it("should construct a widget view of the type dictated by the given model",
      function() {
        var model = widget.WidgetModel.build({type: 'toy'});
        var view = views.make({model: model});

        assert(view instanceof ToyWidgetView);
        assert.strictEqual(view.model, model);
      });
    });

    describe(".addNew", function() {
      it("should add a widget view with the given options", function() {
        var model = widget.WidgetModel.build({type: 'toy'});
        views.addNew({model: model});

        var view = views.findByModel(model);
        assert(view instanceof ToyWidgetView);
        assert.strictEqual(view.model, model);
      });
    });
  });
});
