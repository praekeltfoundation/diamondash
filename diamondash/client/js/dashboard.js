diamondash.dashboard = function() {
  var structures = diamondash.components.structures,
      models = diamondash.models,
      widgets = diamondash.widgets,
      dynamic = diamondash.widgets.dynamic;

  var DashboardRowModel = models.Model.extend({
    relations: [{
      type: Backbone.HasMany,
      key: 'widgets',
      relatedModel: 'diamondash.widgets.widget.WidgetModel',
      includeInJSON: ['name']
    }]
  });

  var DashboardModel = models.Model.extend({
    relations: [{
      type: Backbone.HasMany,
      key: 'widgets',
      relatedModel: 'diamondash.widgets.widget.WidgetModel',
      reverseRelation: {
        key: 'dashboard',
        includeInJSON: false
      }
    }, {
      type: Backbone.HasMany,
      key: 'rows',
      relatedModel: DashboardRowModel,
      includeInJSON: ['widgets']
    }],

    defaults: {
      widgets: [],
      rows: [],
      poll_interval: 10000
    },

    initialize: function() {
      this.pollHandle = null;
    },

    fetchSnapshots: function(options) {
      this.get('widgets').each(function(m) {
        if (m instanceof dynamic.DynamicWidgetModel) {
          m.fetchSnapshot(options);
        }
      });
    },

    poll: function(options) {
      if (this.pollHandle === null) {
        this.fetchSnapshots(options);

        var self = this;
        this.pollHandle = setInterval(
          function() { self.fetchSnapshots(); },
          this.get('poll_interval'));
      }

      return this;
    },

    stopPolling: function() {
      if (this.pollHandle !== null) {
        clearInterval(this.pollHandle);
        this.pollHandle = null;
      }

      return this;
    }
  });

  var DashboardWidgetViews = structures.SubviewSet.extend({
    parentAlias: 'dashboard',

    selector: function(key) {
      return '[data-widget=' + key + '] .widget-body';
    },

    make: function(options) {
      return widgets.registry.views.make(options);
    }
  });

  var DashboardView = Backbone.View.extend({
    jst: JST['diamondash/client/jst/dashboard.jst'],

    initialize: function() {
      this.widgets = new DashboardWidgetViews({dashboard: this});

      this.model.get('widgets').each(function(w) {
        this.widgets.add({model: w});
      }, this);
    },

    render: function() {
      this.$el.html(this.jst({dashboard: this}));
      this.widgets.render();
      return this;
    }
  });

  return {
    DashboardView: DashboardView,
    DashboardWidgetViews: DashboardWidgetViews,

    DashboardModel: DashboardModel,
    DashboardRowModel: DashboardRowModel
  };
}.call(this);
