var widgets = diamondash.widgets,
    DashboardController = diamondash.DashboardController;

describe("DashboardController", function(){
  describe(".fromConfig()", function(){
    var dashboard, config;
    
    before(function() {
      widgets.ToyWidgetModelA = widgets.WidgetModel.extend({
        type: 'ToyWidgetModelA'
      });

      widgets.ToyWidgetModelB = widgets.WidgetModel.extend({
        type: 'ToyWidgetModelB'
      });

      widgets.ToyWidgetViewA = widgets.WidgetView.extend({
        type: 'ToyWidgetViewA'
      });

      widgets.ToyWidgetViewB = widgets.WidgetView.extend({
        type: 'ToyWidgetViewB'
      });
    });

    after(function() {
      delete widgets.ToyWidgetModelA;
      delete widgets.ToyWidgetViewA;
      delete widgets.ToyWidgetModelB;
      delete widgets.ToyWidgetViewB;
    });

    beforeEach(function() {
      config = {
        name: 'tatooine-the-dashboard',
        requestInterval: 10,
        widgets: [{
          model: {name: 'anakin-the-widget'},
          modelClass: "ToyWidgetModelA",
          viewClass: "ToyWidgetViewA"
        }, {
          model: {name: 'qui-gon-the-widget'},
          modelClass: "ToyWidgetModelB",
          viewClass:"ToyWidgetViewB"}]};
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
      assert.equal(dashboard.widgetViews[0].model,
                   dashboard.widgets.at(0));
      assert.equal(dashboard.widgetViews[1].model,
                   dashboard.widgets.at(1));
    });
  });
});
