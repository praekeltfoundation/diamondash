diamondash.widgets = function() {
  var structures = diamondash.components.structures;

  var registry = {
    models: new structures.Registry(),
    views: new structures.Registry()
  };

  var WidgetViewSet = structures.ViewSet.extend({
    make: function(options) {
      var type;

      if (options.model) {
        type = registry.views.get(options.model.get('type_name'));
      }

      type = type || diamondash.widgets.widget.WidgetView;
      return new type(options);
    },

    ensure: function(obj) {
      return !(obj instanceof Backbone.View)
        ? this.make(obj)
        : obj;
    }
  });

  return {
    registry: registry,
    WidgetViewSet: WidgetViewSet
  };
}.call(this);
