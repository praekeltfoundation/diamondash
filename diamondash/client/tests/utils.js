diamondash.test.utils = function() {
  function unregisterModels() {
    // Accessing an internal variable is not ideal, but Backbone.Relational
    // doesn't offer a way to unregister all its store's models or access all
    // its store's collections
    var collections = Backbone.Relational.store._collections;
    collections.forEach(function(c) { c.reset([], {remove: true}); });
    Backbone.Relational.store._collections = [];
  }

  function hover_svg(chart, coords) {
    coords = _(coords || {}).defaults({x: 0, y: 0});
    chart.trigger('hover', chart.positionOf(coords));
  }

  function hover_axes(chart, coords) {
    coords = _(coords || {}).defaults({x: 0, y: 0});

    hover_svg(chart, {
      x: chart.fx(coords.x),
      y: chart.fy(coords.y)
    });
  }

  return {
    hover_svg: hover_svg,
    hover_axes: hover_axes,
    unregisterModels: unregisterModels
  };
}.call(this);
