diamondash.widgets = function() {
  var structures = diamondash.components.structures;

  var WidgetRegistry = structures.Registry.extend({
    processAdd: function(name, options) {
      return _({}).defaults(options, {
        view: diamondash.widgets.widget.WidgetView,
        model: diamondash.widgets.widget.WidgetModel
      });
    }
  });

  return {
    registry: new WidgetRegistry(),
    WidgetRegistry: WidgetRegistry
  };
}.call(this);
