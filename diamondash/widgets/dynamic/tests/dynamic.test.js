describe("diamondash.widgets.dynamic", function() {
  var dynamic = diamondash.widgets.dynamic,
      utils = diamondash.test.utils;

  afterEach(function() {
    utils.unregisterModels();
  });

  describe(".DynamicWidgetModel", function() {
    var model,
        server;

    beforeEach(function() {
      server = sinon.fakeServer.create();

      model = new dynamic.DynamicWidgetModel({
        name: 'widget-1',
        width: 2,
        type_name: 'dynamic',
        foo: [1, 2, 3],
        bar: ['a', 'b', 'c'],
        dashboard: {name: 'dashboard-1'}
      });
    });

    afterEach(function() {
      server.restore();
    });

    describe(".snapshotUrl()", function() {
      it("should construct the snapshot url correctly", function() {
        var config = diamondash.config;
        config.set('url_prefix', 'foo');

        assert.equal(
          model.snapshotUrl(),
          '/foo/api/widgets/dashboard-1/widget-1/snapshot');

        config.set('url_prefix', config.previous('url_prefix'));
      });
    });

    describe(".fetchSnapshot()", function() {
      it("should issue an api request to its snapshot url", function(done) {
        server.respondWith(function(req) {
          assert.equal(req.url, '/api/widgets/dashboard-1/widget-1/snapshot');
          done();
        });

        model.fetchSnapshot();
        server.respond();
      });

      it("should not remove attrs not present in the api response",
      function() {
        server.respondWith(JSON.stringify({foo: 'spam'}));

        model.fetchSnapshot();
        server.respond();

        assert.deepEqual(model.toJSON(), {
          name: 'widget-1',
          width: 2,
          type_name: 'dynamic',
          foo: 'spam',
          bar: ['a', 'b', 'c']
        });
      });
    });
  });
});
