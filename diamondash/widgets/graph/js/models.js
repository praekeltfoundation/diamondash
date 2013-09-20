diamondash.widgets.graph.models = function() {
  var widget = diamondash.widgets.widget,
      structures = diamondash.components.structures,
      utils = diamondash.utils;

  var GraphMetricModel = Backbone.RelationalModel.extend({
    idAttribute: 'name',

    defaults: {
      'datapoints': [],
    },

    bisect: d3
      .bisector(function(d) { return d.x; })
      .left,

    lastValue: function(x) {
      var datapoints = this.get('datapoints'),
          d = datapoints[datapoints.length - 1];

      return d && typeof d.y !== 'undefined'
        ? d.y
        : null;
    },

    valueAt: function(x) {
      var datapoints = this.get('datapoints'),
          i = this.bisect(datapoints, x);
          d = datapoints[i];

      return d && x === d.x
        ? d.y
        : null;
    }
  });

  var GraphMetricCollection = Backbone.Collection.extend({
    colorOptions: {
      n: 10,
      scale: d3.scale.category10()
    },

    initialize: function() {
      this.colors = new structures.ColorMaker(this.colorOptions);
      utils.bindEvents(this.bindings, this);
    },

    bindings: {
      'add': function(metric) {
        metric.set('color', this.colors.next());
      }
    }
  });

  var GraphModel = widget.WidgetModel.extend({
    isStatic: false,

    relations: [{
      type: Backbone.HasMany,
      key: 'metrics',
      relatedModel: GraphMetricModel,
      collectionType: GraphMetricCollection
    }],

    defaults: {
      'domain': 0,
      'range': 0,
      'metrics': []
    },
  });

  return {
    GraphModel: GraphModel,
    GraphMetricModel: GraphMetricModel,
    GraphMetricCollection: GraphMetricCollection,
  };
}.call(this);
