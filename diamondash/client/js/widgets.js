diamondash.widgets = function() {
  function WidgetRegistry(widgets) {
    this.widgets = {};
    
    _(widgets || {}).each(function(options, name) {
      this.add(name, options);
    }, this);
  };

  WidgetRegistry.prototype = {
    add: function(name, options) {
      if (name in this.widgets) {
        throw new Error("Widget type '" + name + "' already exists.");
      }

      options = options || {};
      this.widgets[name] = {
        view: options.view || diamondash.widgets.widget.WidgetView,
        model: options.model || diamondash.widgets.widget.WidgetModel
      };
    },

    get: function(name) {
      return this.widgets[name];
    },

    remove: function(name) {
      var widget = this.get(name);
      delete this.widgets[name];
      return widget;
    }
  };

  return {
    registry: new WidgetRegistry(),
    WidgetRegistry: WidgetRegistry
  };
}.call(this);
