diamondash.widgets.widget = function() {
  var widgets = diamondash.widgets;

  var WidgetModel = Backbone.RelationalModel.extend({
    idAttribute: 'name',

    subModelTypes: {},

    url: function() {
      return [
        '/api',
        'widgets',
        this.get('dashboardName'),
        this.get('name')
      ].join('/');
    }
  });

  var WidgetCollection = Backbone.Collection.extend({
    model: WidgetModel
  });

  var WidgetView = Backbone.View.extend({
  });

  widgets.registry.models.add('widget', WidgetModel);
  widgets.registry.views.add('widget', WidgetView);

  widgets.registry.models.on('add', function(name, type) {
    var objName = 'diamondash.widgets.registry.models.items.' + name;

    // Modifying something on the prototype and changing internal properties
    // set by backbone-relational is not ideal, but is the only way to
    // dynamically add/remove sub-models without changing backbone-relational
    WidgetModel.prototype.subModelTypes[name] = objName;
    WidgetModel._subModels[name] = type;
  });

  widgets.registry.models.on('remove', function(name) {
    delete WidgetModel.prototype.subModelTypes[name];
    delete WidgetModel._subModels[name];
  });

  return {
    WidgetModel: WidgetModel,
    WidgetCollection: WidgetCollection,
    WidgetView: WidgetView
  };
}.call(this);
