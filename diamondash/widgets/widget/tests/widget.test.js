var WidgetModel = diamondash.widgets.WidgetModel;

describe("WidgetModel", function() {
  describe(".url()", function() {
    it("should construct the correct render url.", function() {
      var model = new WidgetModel({
        name: 'some-widget',
        dashboardName: 'some-dashboard'
      });
      assert.equal(model.url(), '/render/some-dashboard/some-widget');
    });
  });

  describe(".fetch()", function() {
    it("should only fetch data if the model isnt static.", function() {
      var StaticWidgetModel, DynamicWidgetModel, model;

      StaticWidgetModel = WidgetModel.extend({isStatic: true});
      DynamicWidgetModel = WidgetModel.extend({isStatic: false});

      model = new StaticWidgetModel({
        name: 'some-widget',
        dashboardName: 'some-dashboard'
      });
      sinon.stub(model, '_fetch');
      model.fetch();
      assert.equal(model._fetch.called, false);

      model = new DynamicWidgetModel({
        name: 'some-widget',
        dashboardName: 'some-dashboard'
      });
      sinon.stub(model, '_fetch');
      model.fetch();
      assert(model._fetch.called);
    });
  });
});
