var assert = require('assert'),
    widget = require('widgets/widget/widget'),
    dashboard = require('../dashboard'),
    DashboardController = dashboard.DashboardController;

describe('DashboardController', function(){
    describe('.fromConfig()', function(){
        var dashboard, config;

        beforeEach(function() {
            config = {
                requestInterval: 10,
                widgets: [{
                    name: 'anakin-the-widget',
                    model: {
                        modulePath: "tests/dashboard.test",
                        className: "ToyWidgetModelA"},
                    view: {
                        modulePath: "tests/dashboard.test",
                        className: "ToyWidgetViewA"}}, {
                    name: 'qui-gon-the-widget',
                    model: {
                        modulePath: "tests/dashboard.test",
                        className: "ToyWidgetModelB"},
                    view: {
                        modulePath: "tests/dashboard.test",
                        className: "ToyWidgetViewB"}}]};
        });

        it('should create the widget model collection correctly', function() {
            dashboard = DashboardController.fromConfig(config);
            assert.equal(dashboard.widgets.get('anakin-the-widget').type,
                         'ToyWidgetModelA');
            assert.equal(dashboard.widgets.get('qui-gon-the-widget').type,
                         'ToyWidgetModelB');
        });

        it('should create the widget views correctly', function() {
            dashboard = DashboardController.fromConfig(config);
            assert.equal(dashboard.widgetViews[0].type, 'ToyWidgetViewA');
            assert.equal(dashboard.widgetViews[1].type, 'ToyWidgetViewB');
            //assert.equal(dashboard.widgetViews[0].el, '#anakin-the-widget');
            //assert.equal(dashboard.widgetViews[1].el, '#qui-gon-the-widget');
            assert.equal(dashboard.widgetViews[0].model,
                         dashboard.widgets.at(0));
            assert.equal(dashboard.widgetViews[1].model,
                         dashboard.widgets.at(1));
        });

        it('should set the request interval correctly', function() {
            dashboard = DashboardController.fromConfig(config);
            assert.equal(dashboard.requestInterval, 10);

            config = {widgets: []};
            dashboard = DashboardController.fromConfig(config);
            assert.equal(dashboard.requestInterval,
                         DashboardController.DEFAULT_REQUEST_INTERVAL);
            
        });
    });
});

var ToyWidgetModelA = widget.WidgetModel.extend({
    type: 'ToyWidgetModelA'
});

var ToyWidgetModelB = widget.WidgetModel.extend({
    type: 'ToyWidgetModelB'
});

var ToyWidgetViewA = widget.WidgetView.extend({
    type: 'ToyWidgetViewA'
});

var ToyWidgetViewB = widget.WidgetView.extend({
    type: 'ToyWidgetViewB'
});

module.exports = {
    ToyWidgetModelA: ToyWidgetModelA,
    ToyWidgetModelB: ToyWidgetModelB,
    ToyWidgetViewA: ToyWidgetViewA,
    ToyWidgetViewB: ToyWidgetViewB
};
