describe("diamondash.widgets", function() {
  var widgets = diamondash.widgets;

  describe("WidgetRegistry", function() {
    var ToyWidgetModelA = widgets.widget.WidgetModel.extend({}),
        ToyWidgetModelB = widgets.widget.WidgetModel.extend({}),
        ToyWidgetViewA = widgets.widget.WidgetView.extend({}),
        ToyWidgetViewB = widgets.widget.WidgetView.extend({});

    var registry;

    beforeEach(function() {
      registry = new widgets.WidgetRegistry({
        a: {model: ToyWidgetModelA, view: ToyWidgetViewA}
      });
    });

    describe(".add", function() {
      it("should register a widget type", function() {
        registry.add('b', {
          model: ToyWidgetModelB,
          view: ToyWidgetViewB,
        });

        assert.equal(registry.widgets.b.model, ToyWidgetModelB);
        assert.equal(registry.widgets.b.view, ToyWidgetViewB);
      });

      it("should throw an error if the widget type already exists",
      function() {
        assert.throws(function() {
          registry.add('a', {
            model: ToyWidgetModelB,
            view: ToyWidgetViewB,
          });
        }, /Widget type 'a' already exists/);
      });
    });

    describe(".get", function() {
      it("should retrieve the widget type", function() {
        assert.deepEqual(
          registry.get('a'),
          {model: ToyWidgetModelA, view: ToyWidgetViewA});
      });
    });

    describe(".remove", function() {
      it("should remove the widget from the registry", function() {
        assert('a' in registry.widgets);
        assert.equal(registry.get('a'), registry.remove('a'));
        assert(!('a' in registry.widgets));
      });
    });
  });
});
