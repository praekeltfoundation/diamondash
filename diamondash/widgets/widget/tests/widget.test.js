describe("diamondash.widgets", function() {
  var widget = diamondash.widgets.widget,
      utils = diamondash.test.utils;

  afterEach(function() {
    utils.unregisterModels();
  });

  describe("WidgetModel", function() {
    var WidgetModel = widget.WidgetModel;

    var model;

    beforeEach(function() {
        model = new WidgetModel({
          name: 'some-widget',
          dashboardName: 'some-dashboard'
        });
    });

    describe(".url()", function() {
      it("should construct the correct snapshot url.", function() {
        assert.equal(
          model.url(), '/api/widgets/some-dashboard/some-widget/snapshot');
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
});
