diamondash.dashboard = function() {
  var widgets = diamondash.widgets,
      widget = diamondash.widgets.widget,
      dynamic = diamondash.widgets.dynamic;

  var DashboardModel = Backbone.RelationalModel.extend({
    relations: [{
      type: Backbone.HasMany,
      key: 'widgets',
      relatedModel: 'diamondash.widgets.widget.WidgetModel',
      reverseRelation: {
        key: 'dashboard',
        includeInJSON: false
      }
    }],

    defaults: {
      widgets: [],
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
      var self = this;

      if (this.pollHandle === null) {
        this.fetchSnapshots(options);

        this.pollHandle = setInterval(
          function() { self.fetchSnapshots(); },
          this.get('poll_interval'));
      }

      return this;
    },

    stopPolling: function() {
      if (this.pollHandle !== null) {
        clearInterval(this.pollHandle);
      }

      return this;
    }
  });

  var DashboardView = Backbone.View.extend({
    initialize: function() {
      this.widgets = new widgets.WidgetViewSet();

      this.model.get('widgets').each(function(w) {
        this.widgets.addNew({
          el: '#' + w.id,
          model: w
        });
      }, this);
    },
  });

  return {
    DashboardView: DashboardView,
    DashboardModel: DashboardModel
  };
}.call(this);
