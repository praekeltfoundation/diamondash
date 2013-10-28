diamondash.widgets = function() {
  var structures = diamondash.components.structures;

  var WidgetViewRegistry = structures.Registry.extend({
    make: function(options) {
      var type;

      if (options.model) {
        type = this.get(options.model.get('type_name'));
      }

      type = type || diamondash.widgets.widget.WidgetView;
      return new type(options);
    }
  });

  var registry = {
    models: new structures.Registry(),
    views: new WidgetViewRegistry()
  };

  return {
    registry: registry,
    WidgetViewRegistry: WidgetViewRegistry
  };
}.call(this);
