var widget = require('widgets/widget/widget');
var lvalue = require('widgets/lvalue/lvalue-widget');

module.exports = {

  DashboardController: function() {
    var loadClass;

    function DashboardController(args) {
      this.name = args.name;
      this.widgets = args.widgets;
      this.widgetViews = args.widgetViews;
      this.requestInterval = args.requestInterval;
    }

    DashboardController.DEFAULT_REQUEST_INTERVAL = 10000;

    DashboardController.fromConfig = function(config) {
      var dashboardName, requestInterval, widgets, widgetViews;

      dashboardName = config.name;

      requestInterval = (config.requestInterval ||
                         DashboardController.DEFAULT_REQUEST_INTERVAL);

      widgets = new widget.WidgetCollection();
      widgetViews = [];

      config.widgets.forEach(function(widgetConfig) {
        var Model, View, name, model, view;

        Model = loadClass(widgetConfig.model);
        View = loadClass(widgetConfig.view);
        name = widgetConfig.name;
        model = new Model({name: name, dashboardName: dashboardName});
        view = new View({el: "#" + name, model: model});

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

    DashboardController.prototype = {
      start: function() {
        var self = this;
        var fetch = function(model) { return model.fetch(); };
        setInterval(function() { self.widgets.forEach(fetch); },
                    this.requestInterval);
      }
    };

    loadClass = function(config) {
      return require(config.modulePath)[config.className];
    };

    return DashboardController;
  }()

};
