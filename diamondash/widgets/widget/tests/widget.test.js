var WidgetModel = diamondash.widgets.WidgetModel;

describe("WidgetModel", function() {
  var model;

  beforeEach(function() {
      model = new WidgetModel({
        name: 'some-widget',
        dashboardName: 'some-dashboard'
      });
  });

  describe(".url()", function() {
    it("should construct the correct render url.", function() {
      assert.equal(model.url(), '/render/some-dashboard/some-widget');
    });
  });

  describe(".fetch()", function() {
    it("should not fetch data if the model is static.", function() {
      function assertFetched(fetched) {
        sinon.stub(model, '_fetch');
        model.fetch();
        assert.equal(model._fetch.called, fetched);
        model._fetch.restore();
      }

      model.isStatic = true;
      assertFetched(false);

      model.isStatic = false;
      assertFetched(true);
    });
  });

  describe(".parse()", function() {
    it("Should only parse truthy, non-empty responses", function() {
      function assertParsed(response, parsed) {
        sinon.stub(model, '_parse');
        model.parse(response, {});
        assert.equal(model._parse.called, parsed);
        model._parse.restore();
      }

      assertParsed({}, false);
      assertParsed(undefined, false);
      assertParsed(null, false);
      assertParsed({x: 1}, true);
    });
  });
});
