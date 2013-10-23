describe("diamondash.widgets", function(){
  var widgets = diamondash.widgets,
      widget = diamondash.widgets.widget;

  var ToyWidgetView = Backbone.View.extend();

  describe(".WidgetViewRegistry", function() {
    var views;

    beforeEach(function() {
      views = new widgets.WidgetViewRegistry();
      views.add('toy', ToyWidgetView);
    });

    describe(".make()", function() {
      it("should construct a widget view of the type dictated by the given model",
      function() {
        var model = widget.WidgetModel.build({type_name: 'toy'});
        var view = views.make({model: model});

        assert(view instanceof ToyWidgetView);
        assert.strictEqual(view.model, model);
      });
    });
  });
});
