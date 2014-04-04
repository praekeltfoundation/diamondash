diamondash.widgets.pie.views = function() {
  var PieView = Backbone.View.extend({
  });

  widgets.registry.views.add('pie', PieView);

  return {
    PieView: PieView
  };
}.call(this);
