var Backbone = require('backbone'),
    exports = module.exports = {};

exports.WidgetModel = Backbone.Model.extend({
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

exports.WidgetCollection = Backbone.Collection.extend({
  model: exports.WidgetModel
});

exports.WidgetView = Backbone.View.extend({
});
