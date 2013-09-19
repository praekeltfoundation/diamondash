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
});
