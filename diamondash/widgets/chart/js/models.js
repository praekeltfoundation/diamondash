diamondash.widgets.chart.models = function() {
  var widgets = diamondash.widgets,
      dynamic = diamondash.widgets.dynamic,
      structures = diamondash.components.structures,
      utils = diamondash.utils;

  var ChartMetricModel = Backbone.RelationalModel.extend({
    defaults: {
      datapoints: []
    },

    bisect: d3
      .bisector(function(d) { return d.x; })
      .left,

    lastValue: function(x) {
      var datapoints = this.get('datapoints'),
          d = datapoints[datapoints.length - 1];

      return d && (typeof d.y !== 'undefined')
        ? d.y
        : null;
    },

    valueAt: function(x) {
      var datapoints = this.get('datapoints'),
          i = this.bisect(datapoints, x);
          d = datapoints[i];

      return d && (x === d.x)
        ? d.y
        : null;
    },

    xMin: function() {
      return utils.min(
        this.get('datapoints'),
        function(d) { return d.x; });
    },

    xMax: function() {
      return utils.max(
        this.get('datapoints'),
        function(d) { return d.x; });
    },

    domain: function() {
      return [this.xMin(), this.xMax()];
    },

    yMin: function() {
      return utils.min(
        this.get('datapoints'),
        function(d) { return d.y; });
    },

    yMax: function() {
      return utils.max(
        this.get('datapoints'),
        function(d) { return d.y; });
    },

    range: function() {
      return [this.yMin(), this.yMax()];
    }
  });

  var ChartMetricCollection = Backbone.Collection.extend({
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

  var ChartModel = dynamic.DynamicWidgetModel.extend({
    relations: [{
      type: Backbone.HasMany,
      key: 'metrics',
      relatedModel: ChartMetricModel,
      collectionType: ChartMetricCollection
    }],

    defaults: {
      'metrics': []
    },

    xMin: function() {
      return utils.min(this.get('metrics').map(function(m) {
        return m.xMin();
      }));
    },

    xMax: function() {
      return utils.max(this.get('metrics').map(function(m) {
        return m.xMax();
      }));
    },

    domain: function() {
      return [this.xMin(), this.xMax()];
    },

    yMin: function() {
      return utils.min(this.get('metrics').map(function(m) {
        return m.yMin();
      }));
    },

    yMax: function() {
      return utils.max(this.get('metrics').map(function(m) {
        return m.yMax();
      }));
    },

    range: function() {
      return [this.yMin(), this.yMax()];
    }
  });

  widgets.registry.models.add('chart', ChartModel);

  return {
    ChartModel: ChartModel,
    ChartMetricModel: ChartMetricModel,
    ChartMetricCollection: ChartMetricCollection,
  };
}.call(this);
