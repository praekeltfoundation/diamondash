var assert = require('assert'),
widget = require('widgets/widget/widget'),
dashboard = require('../dashboard'),
DashboardController = dashboard.DashboardController;

describe("DashboardController", function(){
  describe(".fromConfig()", function(){
    var dashboard, config;

    beforeEach(function() {
      config = {
        name: 'tatooine-the-dashboard',
        requestInterval: 10,
        widgets: [{
          model: {
            name: 'anakin-the-widget'},
          modelClass: {
            modulePath: "tests/dashboard.test",
            className: "ToyWidgetModelA"},
          viewClass: {
            modulePath: "tests/dashboard.test",
            className: "ToyWidgetViewA"}}, {

          model: {
            name: 'qui-gon-the-widget'},
          modelClass: {
            modulePath: "tests/dashboard.test",
            className: "ToyWidgetModelB"},
          viewClass: {
            modulePath: "tests/dashboard.test",
            className: "ToyWidgetViewB"}}]};
    });

    it("should create the widget model collection correctly", function() {
      dashboard = DashboardController.fromConfig(config);
      assert.equal(dashboard.widgets.get('anakin-the-widget').type,
                   'ToyWidgetModelA');
      assert.equal(dashboard.widgets.get('qui-gon-the-widget').type,
                   'ToyWidgetModelB');
    });

    it("should create the widget views correctly", function() {
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

    it("should set the request interval correctly", function() {
      dashboard = DashboardController.fromConfig(config);
      assert.equal(dashboard.requestInterval, 10);

      config = {widgets: []};
      dashboard = DashboardController.fromConfig(config);
      assert.equal(dashboard.requestInterval,
                   DashboardController.DEFAULT_REQUEST_INTERVAL);

    });

    it("should set the dashboard name", function() {
      dashboard = DashboardController.fromConfig(config);
      assert.equal(dashboard.name, 'tatooine-the-dashboard');
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
