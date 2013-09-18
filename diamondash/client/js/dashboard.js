diamondash.dashboard = function() {
  WidgetCollection = diamondash.widgets.widget.WidgetCollection;

  function DashboardController(args) {
    this.name = args.name;
    this.widgets = args.widgets;
    this.widgetViews = args.widgetViews;
    this.requestInterval = args.requestInterval;
  }

  DashboardController.DEFAULT_REQUEST_INTERVAL = 10000;

  DashboardController.fromConfig = function(config) {
    var dashboardName = config.name;

    var widgets = new WidgetCollection(),
        widgetViews = [];

    var requestInterval = config.requestInterval
                       || DashboardController.DEFAULT_REQUEST_INTERVAL;

    config.widgets.forEach(function(widgetConfig) {
      var widgetType = diamondash.widgets.registry.get(widgetConfig.typeName);

      var model = new widgetType.model(
        _({dashboardName: dashboardName}).extend(widgetConfig.model),
        {collection: widgets});

      widgets.add(model);

      widgetViews.push(new widgetType.view({
        el: $("#" + model.get('name')),
        model: model,
        config: widgetConfig.view
      }));
    });

    return new DashboardController({
      name: dashboardName,
      widgets: widgets,
      widgetViews: widgetViews,
      requestInterval: requestInterval
    });
  };

  DashboardController.prototype = {
    fetch: function() {
      this.widgets.forEach(function(m) { return m.fetch(); });
    },
    start: function() {
      var self = this;

      self.fetch();
      setInterval(
        function() { self.fetch.call(self); },
        this.requestInterval);
    }
  };

  return {
    DashboardController: DashboardController
  };
}.call(this);
