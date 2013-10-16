diamondash.widgets.widget = function() {
  var widgets = diamondash.widgets;

  var WidgetModel = Backbone.RelationalModel.extend({
    idAttribute: 'name',

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

  return {
    WidgetModel: WidgetModel,
    WidgetCollection: WidgetCollection,
    WidgetView: WidgetView
  };
}.call(this);
