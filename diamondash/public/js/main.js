function DashboardController(widgets, widgetViews, requestInterval) {
    this.widgets = widgets;
    this.widgetViews = widgetViews;
}

DashboardController.REQUEST_INTERVAL = 10000;

DashboardController.fromConfig = function(config) {
    var requestInterval = config.requestInterval || this.REQUEST_INTERVAL;

    var widgets = new WidgetCollection();
    var widgetViews = [];

    config.widgets.forEach(function(widgetConfig) {
        var Model = window[widgetConfig.model],
            View = window[widgetConfig.view];

        var name = widgetConfig.name,
            model = new Model({name: name}),
            view = new View({el: "#" + name, model: model});

        widgetViews.push(view);
        widgets.add(model);
    });

    return new DashboardController(widgets, widgetViews, requestInterval);
};

DashboardController.prototype = {
    start: function() {
        console.log('larp');
        // TODO
    }
};
