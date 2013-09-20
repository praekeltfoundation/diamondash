diamondash.widgets = function() {
  var structures = diamondash.components.structures,
      utils = diamondash.utils;

  var WidgetRegistry = structures.Registry.extend({
    processAdd: function(name, options) {
      return _({}).defaults(options, {
        view: 'diamondash.widgets.widget.WidgetView',
        model: 'diamondash.widgets.widget.WidgetModel'
      });
    },

    processGet: function(name, options) {
      return {
        view: utils.maybeByName(options.view),
        model: utils.maybeByName(options.model)
      };
    }
  });

  return {
    registry: new WidgetRegistry(),
    WidgetRegistry: WidgetRegistry
  };
}.call(this);
