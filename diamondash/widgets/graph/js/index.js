diamondash.widgets.graph = function() {
  diamondash.widgets.registry.add('graph', {
    model: 'diamondash.widgets.graph.models.GraphModel',
    view: 'diamondash.widgets.graph.views.GraphView'
  });

  return {
  };
}.call(this);
