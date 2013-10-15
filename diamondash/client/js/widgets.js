diamondash.widgets = function() {
  var structures = diamondash.components.structures;

  var registry = {
    models: new structures.Registry(),
    views: new structures.Registry()
  };

  return {
    registry: registry
  };
}.call(this);
