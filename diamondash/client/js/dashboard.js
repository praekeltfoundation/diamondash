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
          dashboardName,
          requestInterval,
          widgets,
          widgetViews;

      dashboardName = config.name;

      requestInterval = (config.requestInterval ||
                         DashboardController.DEFAULT_REQUEST_INTERVAL);

      widgets = new diamondashWidgets.WidgetCollection();
      widgetViews = [];

      config.widgets.forEach(function(widgetConfig) {
        var modelClass = diamondashWidgets[widgetConfig.modelClass];
        var modelConfig = widgetConfig.model;
        modelConfig.dashboardName = dashboardName;
        var model = new modelClass(modelConfig);

        var viewClass = diamondashWidgets[widgetConfig.viewClass];
        var view = new viewClass({
          el: $("#" + model.get('name') + ' .widget-container'),
          model: model,
          config: widgetConfig.view
        });

        widgetViews.push(view);
        widgets.add(model);
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
