diamondash.test = {};

diamondash.test.utils = function() {
  function unregisterModels() {
    // Accessing an internal variable is not ideal, but Backbone.Relational
    // doesn't offer a way to unregister all its store's models or access all
    // its store's collections
    var collections = Backbone.Relational.store._collections;
    collections.forEach(function(c) { c.reset([], {remove: true}); });
    Backbone.Relational.store._collections = [];
  };

  return {
    unregisterModels: unregisterModels
  };
}.call(this);
