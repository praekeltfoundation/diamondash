describe("diamondash.dashboard", function(){
  var widgets = diamondash.widgets,
      utils = diamondash.test.utils;

  afterEach(function() {
    utils.unregisterModels();
  });

  describe("DashboardController", function(){
    var DashboardController = diamondash.dashboard.DashboardController;

    describe(".fromConfig()", function(){
      var dashboard, config;
      
      before(function() {
        widgets.toy = {};

        widgets.toy.ToyWidgetModelA = widgets.widget.WidgetModel.extend({
          type: 'ToyWidgetModelA'
        });

        widgets.toy.ToyWidgetModelB = widgets.widget.WidgetModel.extend({
          type: 'ToyWidgetModelB'
        });

        widgets.toy.ToyWidgetViewA = widgets.widget.WidgetView.extend({
          type: 'ToyWidgetViewA'
        });

        widgets.toy.ToyWidgetViewB = widgets.widget.WidgetView.extend({
          type: 'ToyWidgetViewB'
        });
      });

      after(function() {
        delete widgets.toy;
      });

      beforeEach(function() {
        config = {
          name: 'tatooine-the-dashboard',
          requestInterval: 10,
          widgets: [{
            model: {name: 'anakin-the-widget'},
            typeName: "toy",
            modelClass: "ToyWidgetModelA",
            viewClass: "ToyWidgetViewA"
          }, {
            model: {name: 'qui-gon-the-widget'},
            typeName: "toy",
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
});
