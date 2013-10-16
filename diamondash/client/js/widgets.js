diamondash.widgets = function() {
  var utils = diamondash.utils,
      structures = diamondash.components.structures;

  var registry = {
    models: new structures.Registry(),
    views: new structures.Registry()
  };

  var WidgetViewSet = utils.extend(Backbone.ChildViewContainer, {
    make: function(options) {
      var typeName = options.model.get('type');
      var type = registry.views.get(typeName);
      type = type || diamondash.widgets.widget.WidgetView;
      return new type(options);
    },

    addNew: function(options, idx) {
      return this.add(this.make(options), idx);
    }
  });

  return {
    registry: registry,
    WidgetViewSet: WidgetViewSet
  };
}.call(this);
