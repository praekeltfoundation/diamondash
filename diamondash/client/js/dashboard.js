diamondash.dashboard = function() {
  var structures = diamondash.components.structures,
      widgets = diamondash.widgets,
      widget = diamondash.widgets.widget,
      dynamic = diamondash.widgets.dynamic;

  var DashboardRowModel = Backbone.RelationalModel.extend({
    relations: [{
      type: Backbone.HasMany,
      key: 'widgets',
      relatedModel: 'diamondash.widgets.widget.WidgetModel',
      includeInJSON: ['name']
    }]
  });

  var DashboardModel = Backbone.RelationalModel.extend({
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
      return '[data-widget=' + key + '] .body';
    },

    add: function(obj) {
      var widget = widgets.registry.views.ensure(obj);
      return DashboardWidgetViews.__super__.add.call(this, widget);
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
