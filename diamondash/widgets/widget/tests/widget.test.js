describe("diamondash.widgets.widget", function() {
  var widgets = diamondash.widgets,
      widget = diamondash.widgets.widget;

  var ToyWidgetModel = widget.WidgetModel.extend();

  describe("when a widget model is registered", function() {
    before(function() {
      window.ToyWidgetModel = ToyWidgetModel;
    });

    after(function() {
      delete window.ToyWidgetModel;
    });

    afterEach(function() {
      widgets.registry.models.remove('toy');
    });

    it("should add the sub-model type to WidgetModel", function() {
      var model;

      model = widget.WidgetModel.build({type: 'toy'});
      assert(!(model instanceof ToyWidgetModel));

      widgets.registry.models.add('toy', ToyWidgetModel);

      model = widget.WidgetModel.build({type: 'toy'});
      assert(model instanceof ToyWidgetModel);
    });
  });

  describe("when a widget model is unregistered", function() {
    beforeEach(function() {
      widgets.registry.models.add('toy', ToyWidgetModel);
    });

    afterEach(function() {
      widgets.registry.models.remove('toy');
    });

    it("should remove the sub-model type from WidgetModel", function() {
      widgets.registry.models.remove('toy');

      var model = widget.WidgetModel.build({type: 'toy'});
      assert(!(model instanceof ToyWidgetModel));
    });
  });
});
