var widgets = diamondash.widgets;

widgets.WidgetModel = Backbone.Model.extend({
  idAttribute: 'name',
  isStatic: true,

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

  urlRoot: function() {
    return '/render/' + this.get('dashboardName');
  }
});

widgets.WidgetCollection = Backbone.Collection.extend({
  model: widgets.WidgetModel
});

widgets.WidgetView = Backbone.View.extend({
});
