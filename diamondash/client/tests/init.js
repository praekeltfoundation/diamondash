diamondash.test = function() {
  var structures = diamondash.components.structures,
      utils = diamondash.utils;

  var FixtureRegistry = structures.Registry.extend({
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
