describe("diamondash.utils", function() {
  var utils = diamondash.utils;

  describe(".objectByName()", function() {
    it("should get an object defined directly on the context object",
    function() {
      assert.equal(
        utils.objectByName('thing', {thing: 3}),
        3);
    });

    it("should get an object defined on a property of the context object",
    function() {
      assert.equal(
        utils.objectByName('thing.subthing', {thing: {subthing: 23}}),
        23);
    });
  });

  describe(".maybeByName", function() {
    before(function() {
      window.thing = {};
    });

    after(function() {
      delete window.thing;
    });

    it("should return the object if it was reference by name", function() {
      assert.strictEqual(utils.maybeByName('thing'), window.thing);
    });

    it("should return an object if it was passed in", function() {
      var thing = {};
      assert.strictEqual(utils.maybeByName(thing), thing);
    });
  });

  describe(".bindEvents()", function() {
    var thing;

    beforeEach(function() {
      thing = Object.create(Backbone.Events);
    });

    it("should bind events defined on the object itself", function(done) {
      utils.bindEvents({
        'fire': function() { done(); }
      }, thing);

      thing.trigger('fire');
    });

    it("should bind events defined on nested objects", function(done) {
      thing.subthing = {subsubthing: Object.create(Backbone.Events)};

      utils.bindEvents({
        'fire subthing.subsubthing': function() { done(); }
      }, thing);

      thing.subthing.subsubthing.trigger('fire');
    });
  });

  describe(".functor()", function() {
    it("should return the function if it was passed in", function() {
      var fn = function() {};
      assert.equal(utils.functor(fn), fn);
    });

    it("should wrap a non-function as a function", function() {
      assert.equal(utils.functor(3)(), 3);
    });
  });

  describe(".snap()", function() {
    it("should snap the value to the closest step", function() {
      assert.equal(utils.snap(12, 10, 5), 10);
      assert.equal(utils.snap(13, 10, 5), 15);
      assert.equal(utils.snap(15, 10, 5), 15);
      assert.equal(utils.snap(17, 10, 5), 15);
      assert.equal(utils.snap(18, 10, 5), 20);
    });
  });

  describe(".d3Map()", function() {
    it("should perform a map on the selection using the given function",
    function() {
      var stuff = d3.select($('<div>').get(0))
        .selectAll('.stuff')
        .data(['a', 'b', 'c']);

      stuff.enter()
        .append('div')
        .attr('id', function(d) { return d; });

      var n = 0;
      var result = utils.d3Map(stuff, function(d, i) {
        assert.equal(d3.select(this).attr('id'), d);
        assert.equal(i, n++);
        return d;
      });

      assert.deepEqual(result, ['a', 'b', 'c']);
    });
  });

  describe(".joinPaths()", function() {
    it("should join the given paths", function() {
      assert.equal(utils.joinPaths('a', 'b', 'c'), 'a/b/c');
    });

    it("should strip off unwanted slashes", function() {
      assert.equal(utils.joinPaths('a/', '/b/', '/c'), 'a/b/c');
      assert.equal(utils.joinPaths('a/', 'b', '/c'), 'a/b/c');
      assert.equal(utils.joinPaths('a/', '/', 'b', '/', '/c'), 'a/b/c');
      assert.equal(utils.joinPaths('a/', '/b//', '///', '///c'), 'a/b/c');
    });

    it("should keep a slash at the end of the joined path", function() {
      assert.equal(utils.joinPaths('/'), '/');
      assert.equal(utils.joinPaths('a/'), 'a/');
      assert.equal(utils.joinPaths('a/', '/b/', '/c/'), 'a/b/c/');
      assert.equal(utils.joinPaths('a/', '/b/', '/c', '/'), 'a/b/c/');
    });

    it("should keep a slash at the start of the joined path", function() {
      assert.equal(utils.joinPaths('/'), '/');
      assert.equal(utils.joinPaths('/a/', '/b/', '/c/'), '/a/b/c/');
      assert.equal(utils.joinPaths('/', 'a/', '/b/', '/c'), '/a/b/c');
    });
  });
});
