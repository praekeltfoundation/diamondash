diamondash.widgets = function() {
  var utils = diamondash.utils;

  var WidgetRegistry = utils.Registry.extend({
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
