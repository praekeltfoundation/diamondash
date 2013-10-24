diamondash.widgets.dynamic = function() {
  var widgets = diamondash.widgets,
      widget = diamondash.widgets.widget;

  var DynamicWidgetModel = widget.WidgetModel.extend({
    snapshotUrl: function() {
      return diamondash.url(_(this).result('url'), 'snapshot');
    },

    fetchSnapshot: function(options) {
      options = options || {};
      options.url = _(this).result('snapshotUrl');
      
      return this.fetch(options);
    }
  });

  widgets.registry.models.add('dynamic', DynamicWidgetModel);

  return {
    DynamicWidgetModel: DynamicWidgetModel
  };
}.call(this);
