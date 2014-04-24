diamondash.test.utils = function() {
  function unregisterModels() {
    // Accessing an internal variable is not ideal, but Backbone.Relational
    // doesn't offer a way to unregister all its store's models or access all
    // its store's collections
    var collections = Backbone.Relational.store._collections;
    collections.forEach(function(c) { c.reset([], {remove: true}); });
    Backbone.Relational.store._collections = [];
  }

  function hover(chart, coords) {
    coords = _(coords || {}).defaults({x: 0, y: 0});
    chart.trigger('hover', chart.positionOf(coords));
  }

  hover.inverse = function(chart, coords) {
    coords = _(coords || {}).defaults({x: 0, y: 0});

    this(chart, {
      x: chart.fx(coords.x),
      y: chart.fy(coords.y)
    });
  };

  return {
    hover: hover,
    unregisterModels: unregisterModels
  };
}.call(this);
