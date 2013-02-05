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

  urlRoot: function() {
    return '/render/' + this.get('dashboardName');
  }
});

widgets.WidgetCollection = Backbone.Collection.extend({
  model: widgets.WidgetModel
});

widgets.WidgetView = Backbone.View.extend({
});
