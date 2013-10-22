diamondash.dashboard = function() {
  var widgets = diamondash.widgets,
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

  var DashboardView = Backbone.View.extend({
    initialize: function() {
      this.widgets = new widgets.WidgetViewSet();

      this.model.get('widgets').each(function(w) {
        this.addWidget({
          el: this.$('#' + w.id),
          model: w
        });
      }, this);
    },

    addWidget: function(options) {
      var widget = this.widgets.ensure(options);
      this.widgets.add(widget);
      return this;
    },

    removeWidget: function(widget) {
      this.widgets.remove(widget);
      return this;
    },

    render: function() {
      this.widgets.invoke('render');
      return this;
    }
  });

  return {
    DashboardView: DashboardView,
    DashboardModel: DashboardModel
  };
}.call(this);
