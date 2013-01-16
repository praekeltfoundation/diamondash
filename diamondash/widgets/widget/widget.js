var WidgetModel = Backbone.Model.extend({
	idAttribute: "name"
});

var WidgetCollection = Backbone.Collection.extend({
	model: WidgetModel
});

var WidgetView = Backbone.View.extend({
});
