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
        widgets.registry.models.add('toyA', widgets.widget.WidgetModel.extend({
            type: 'ToyWidgetModelA'
        }));
        widgets.registry.views.add('toyA', widgets.widget.WidgetView.extend({
            type: 'ToyWidgetViewA'
        }));

        widgets.registry.models.add('toyB', widgets.widget.WidgetModel.extend({
            type: 'ToyWidgetModelB'
        }));
        widgets.registry.views.add('toyB', widgets.widget.WidgetView.extend({
            type: 'ToyWidgetViewB'
        }));
      });

      after(function() {
        widgets.registry.models.remove('toyA');
        widgets.registry.views.remove('toyA');

        widgets.registry.models.remove('toyB');
        widgets.registry.views.remove('toyB');
      });

      beforeEach(function() {
        config = {
          name: 'tatooine-the-dashboard',
          requestInterval: 10,
          widgets: [{
            model: {name: 'anakin-the-widget'},
            typeName: "toyA"
          }, {
            model: {name: 'qui-gon-the-widget'},
            typeName: "toyB",
          }]
        };
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
