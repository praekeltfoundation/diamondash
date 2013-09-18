diamondash.widgets.text = function() {
  var widgets = diamondash.widgets;

  var TextModel = widgets.widget.WidgetModel.extend({
    isStatic: true
  });

  widgets.registry.add('text', {model: TextModel});

  return {
    TextModel: TextModel
  };
}.call(this);
