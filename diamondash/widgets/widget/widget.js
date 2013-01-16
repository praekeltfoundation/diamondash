var Backbone = require('backbone'),
    exports = module.exports = {};

exports.WidgetModel = Backbone.Model.extend({
    idAttribute: "name"
});

exports.WidgetCollection = Backbone.Collection.extend({
    model: exports.WidgetModel
});

exports.WidgetView = Backbone.View.extend({
});
