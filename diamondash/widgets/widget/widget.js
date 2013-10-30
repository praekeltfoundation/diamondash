diamondash.widgets.widget = function() {
  var models = diamondash.models,
      widgets = diamondash.widgets;

  var WidgetModel = models.Model.extend({
    idAttribute: 'name',

    subModelTypes: {},
    subModelTypeAttribute: 'type_name',

    url: function() {
      return diamondash.url(
        'api/widgets',
        this.get('dashboard').get('name'),
        this.get('name'));
    },

    defaults: {
      width: 3
    }
  });

  var WidgetCollection = Backbone.Collection.extend({
    model: WidgetModel
  });

  var WidgetView = Backbone.View.extend({
    id: function() {
      return this.model.id;
    }
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
