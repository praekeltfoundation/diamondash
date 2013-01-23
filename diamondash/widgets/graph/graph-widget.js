var Backbone = require('backbone'),
    widget = require("widgets/widget/widget"),
    exports = module.exports = {};

exports.GraphWidgetModel = widget.WidgetModel.extend({
  isStatic: false,

  initialize: function(options) {
    var self = this,
        metrics = new exports.GraphWidgetMetricCollection(options.metrics);

    this.set('metrics', metrics);

    metrics
      .on(
        'all',
        function(eventName) { self.trigger(eventName + ':metrics'); })
      .on(
        'change',
        function() { self.trigger('change'); });
  },

  parse: function(data) {
    this.get('metrics').update(data);
  }
});

exports.GraphWidgetMetricModel = Backbone.Model.extend({
  idAttribute: 'name',

  initialize: function(options) {
    if (typeof options.datapoints === 'undefined') {
      this.set('datapoints', []);
    }
  }
});

exports.GraphWidgetMetricCollection = Backbone.Collection.extend({
  model: exports.GraphWidgetMetricModel
});

exports.GraphWidgetView = widget.WidgetView.extend({
  initialize: function(options) {
    this.model.on('change', this.render, this);
  },

  render: function() {
  }
});
