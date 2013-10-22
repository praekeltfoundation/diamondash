describe("diamondash.components.structures", function() {
  var structures = diamondash.components.structures;

  describe(".Registry", function() {
    var registry;

    beforeEach(function() {
      registry = new structures.Registry({
        a: 'foo',
      });
    });

    describe(".add", function() {
      it("should register a widget type", function() {
        registry.add('b', 'bar');
        assert.equal(registry.items.b, 'bar');
      });

      it("should throw an error if the widget type already exists",
      function() {
        assert.throws(function() {
          registry.add('a', 'baz');
        }, /'a' is already registered/);
      });

      it("emit an 'add' event", function(done) {
        registry.on('add', function(name, data) {
          assert.equal(name, 'b');
          assert.equal(data, 'bar');
          done();
        });

        registry.add('b', 'bar');
      });
    });

    describe(".get", function() {
      it("should retrieve the widget type", function() {
        assert.deepEqual(registry.get('a'), 'foo');
      });
    });

    describe(".remove", function() {
      it("should remove the widget from the registry", function() {
        assert('a' in registry.items);
        assert.equal(registry.get('a'), registry.remove('a'));
        assert(!('a' in registry.items));
      });

      it("emit a 'remove' event", function(done) {
        registry.on('remove', function(name, data) {
          assert.equal(name, 'a');
          assert.equal(data, 'foo');
          done();
        });

        registry.remove('a');
      });
    });
  });

  describe(".ViewSet", function() {
    var views,
        viewA,
        viewB;

    beforeEach(function() {
      views = new structures.ViewSet();

      viewA = new Backbone.View({id: 'a'});
      views.add(viewA);

      viewB = new Backbone.View();
      views.add(viewB, 'b');
    });

    describe(".add()", function() {
      it("should key added views by their id", function() {
        var view = new Backbone.View({id: 'c'});

        assert.isUndefined(views.findByCustom('c'));
        views.add(view);
        assert.strictEqual(views.findByCustom('c'), view);
      });

      it("should allow keying of added views by a custom key", function() {
        var view = new Backbone.View();

        assert.isUndefined(views.findByCustom('c'));
        views.add(view, 'c');
        assert.strictEqual(views.findByCustom('c'), view);
      });
    });

    describe(".get()", function() {
      it("should allow retrieving of views by their id", function() {
        assert.strictEqual(views.get('a'), viewA);
      });

      it("should allow retrieving of views by a custom key", function() {
        assert.strictEqual(views.get('b'), viewB);
      });
    });

    describe(".remove()", function() {
      it("should remove the given view", function() {
        assert.strictEqual(views.get('a'), viewA);
        views.remove(viewA);
        assert.isUndefined(views.get('a'));
      });

      it("should allow removal of views by their id", function() {
        assert.strictEqual(views.get('a'), viewA);
        views.remove('a');
        assert.isUndefined(views.get('a'));
      });

      it("should allow removal of views by a custom key", function() {
        assert.strictEqual(views.get('b'), viewB);
        views.remove('b');
        assert.isUndefined(views.get('b'));
      });
    });
  });
});
