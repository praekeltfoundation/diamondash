diamondash.test = function() {
  var utils = diamondash.utils;

  var FixtureRegistry = utils.Registry.extend({
    processAdd: function(name, data) {
      return utils.functor(data);
    },

    processGet: function(name, fixture) {
      return _.clone(fixture());
    }
  });

  function initialize() {
    window.assert = chai.assert;
  }

  initialize();

  return {
    fixtures: new FixtureRegistry()
  };
}.call(this);
