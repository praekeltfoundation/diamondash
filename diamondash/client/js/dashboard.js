diamondash.DashboardController = (function() {
    function DashboardController(args) {
      this.name = args.name;
      this.widgets = args.widgets;
      this.widgetViews = args.widgetViews;
      this.requestInterval = args.requestInterval;
    }

    DashboardController.DEFAULT_REQUEST_INTERVAL = 10000;

    DashboardController.fromConfig = function(config) {
      var diamondashWidgets = diamondash.widgets,
          dashboardName = config.name;

      var widgets = new diamondashWidgets.WidgetCollection(),
          widgetViews = [];

      var requestInterval = config.requestInterval
                         || DashboardController.DEFAULT_REQUEST_INTERVAL;

      config.widgets.forEach(function(widgetConfig) {
        var modelClass = diamondashWidgets[widgetConfig.modelClass];

        var model = new modelClass(
          _({dashboardName: dashboardName}).extend(widgetConfig.model),
          {collection: widgets});

        var viewClass = diamondashWidgets[widgetConfig.viewClass];

        var view = new viewClass({
          el: $("#" + model.get('name')),
          model: model,
          config: widgetConfig.view
        });

        widgets.add(model);
        widgetViews.push(view);
      });

      return new DashboardController({
        name: dashboardName,
        widgets: widgets,
        widgetViews: widgetViews,
        requestInterval: requestInterval
      });
    };

    var fetchModel = function(model) { return model.fetch(); };

    DashboardController.prototype = {
      fetch: function() { this.widgets.forEach(fetchModel); },
      start: function() {
        var self = this;

        self.fetch();
        setInterval(
          function() { self.fetch.call(self); },
          this.requestInterval);
      }
    };

    return DashboardController;
})();
