var widget = require('widgets/widget/widget');

module.exports = {

    DashboardController: function() {
        var loadClass;

        function DashboardController(widgets, widgetViews, requestInterval) {
            this.widgets = widgets;
            this.widgetViews = widgetViews;
            this.requestInterval = requestInterval;
        }

        DashboardController.DEFAULT_REQUEST_INTERVAL = 10000;

        DashboardController.fromConfig = function(config) {
            var requestInterval, widgets, widgetViews;

            requestInterval = (config.requestInterval ||
                               DashboardController.DEFAULT_REQUEST_INTERVAL);
            widgets = new widget.WidgetCollection(),
            widgetViews = [];

            config.widgets.forEach(function(widgetConfig) {
                var Model, View, name, model, view;

                Model = loadClass(widgetConfig.model);
                View = loadClass(widgetConfig.view);
                name = widgetConfig.name,
                model = new Model({name: name}),
                view = new View({el: "#" + name, model: model});

                widgetViews.push(view);
                widgets.add(model);
            });

            return new DashboardController(widgets, widgetViews,
                                           requestInterval);
        };

        DashboardController.prototype = {
            start: function() {
                console.log('larp');
                // TODO
            }
        };

        loadClass = function(config) {
            return require(config.modulePath)[config.className];
        };

        return DashboardController;
    }()

};
