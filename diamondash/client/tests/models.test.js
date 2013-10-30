describe("diamondash.models", function() {
  var test = diamondash.test,
      models = diamondash.models;

  afterEach(function() {
    test.utils.unregisterModels();
  });

  describe(".AuthModel", function() {
    var model;

    beforeEach(function() {
      model = new models.AuthModel({
        username: 'user',
        password: 'pass'
      });
    });

    describe(".stringify()", function() {
      it("should return a basic auth string from the username and password",
      function() {
        assert.equal(
          model.stringify(),
          'Basic ' + Base64.encode('user:pass'));
      });
    });
  });

  describe(".Model", function() {
    var server,
        reqs,
        auth,
        model;

    var ToyAuthModel = models.AuthModel.extend({
      stringify: function() {
        return this.get('username') + ':' + this.get('password');
      }
    });

    var ToyModel = models.Model.extend({
      url: '/foo'
    });

    beforeEach(function() {
      reqs = [];
      server = sinon.fakeServer.create();
      server.respondWith(function(req) { reqs.push(req); });

      auth = new ToyAuthModel({
        username: 'user',
        password: 'pass'
      });

      diamondash.config.set('auth', auth);

      model = new ToyModel();
    });

    afterEach(function() {
      diamondash.config.set('auth', diamondash.config.previous('auth'));
      server.restore();
    });

    describe(".sync()", function() {
      describe("if the 'auth' option is truthy", function() {
        it("should add an authorization header", function() {
          model.sync('read', model);
          server.respond();

          model.sync('read', model, {auth: true});
          server.respond();

          assert(!('Authorization' in reqs[0].requestHeaders));
          assert.equal(reqs[1].requestHeaders.Authorization, 'user:pass');
        });
      });

      describe("if auth is enabled globally", function() {
        it("should add an authorization header", function() {
          auth.set('all', false);
          model.sync('read', model);
          server.respond();

          auth.set('all', true);
          model.sync('read', model);
          server.respond();

          assert(!('Authorization' in reqs[0].requestHeaders));
          assert.equal(reqs[1].requestHeaders.Authorization, 'user:pass');
        });
      });
    });
  });
});
