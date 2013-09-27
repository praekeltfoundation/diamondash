diamondash.widgets.widget = function() {
  var widgets = diamondash.widgets;

  var WidgetModel = Backbone.RelationalModel.extend({
    idAttribute: 'name',
    isStatic: false,

    _fetch: Backbone.Model.prototype.fetch,
    fetch: function() {
      if (!this.isStatic) {
        this._fetch();
      }
    },

    _parse: Backbone.Model.prototype.parse,
    parse: function(response, options) {
      if (response && !_.isEmpty(response)) {
        return this._parse(response, options);
      }
    },

    url: function() {
      return '/api/widgets/'
        + this.get('dashboardName') + '/'
        + this.get('name')
        + '/snapshot';
    }
  });

  var WidgetCollection = Backbone.Collection.extend({
    model: WidgetModel
  });

  var WidgetView = Backbone.View.extend({
  });

  return {
    WidgetModel: WidgetModel,
    WidgetCollection: WidgetCollection,
    WidgetView: WidgetView
  };
}.call(this);
