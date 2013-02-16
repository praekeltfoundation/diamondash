var widgets = diamondash.widgets;

widgets.LValueWidgetModel = widgets.WidgetModel.extend({
  isStatic: false
});

widgets.LValueWidgetView = widgets.WidgetView.extend({
  slotSelectors: [
    '.lvalue-lvalue-slot',
    '.lvalue-diff-slot',
    '.lvalue-percentage-slot',
    '.lvalue-from-slot',
    '.lvalue-to-slot'
  ],

  initialize: function(options) {
    var $el = this.$el,
        $slots = this.$slots = {};

    this.slotSelectors.forEach(function(s) { $slots[s] = $el.find(s); });
    this.$changeEl = $el.find('.lvalue-change');

    this.model.on('change', this.render, this);
  },

  formatLValue: d3.format(".2s"),
  formatDiff: d3.format("+.3s"),
  formatPercentage: d3.format(".2%"),

  _formatTime: d3.time.format("%d-%m-%Y %H:%M"),
  formatTime: function(t) { return this._formatTime(new Date(t * 1000)); },

  applySlotValues: function(slotValues) {
      var $slots = this.$slots;
      for(var s in slotValues) { $slots[s].text(slotValues[s]); }
  },

  render: function() {
    var model = this.model,
        diff= model.get('diff'),
        $changeEl = this.$changeEl;

    this.applySlotValues({
      '.lvalue-from-slot': this.formatTime(model.get('from')),
      '.lvalue-to-slot': this.formatTime(model.get('to')),
      '.lvalue-lvalue-slot': this.formatLValue(model.get('lvalue')),
      '.lvalue-diff-slot': this.formatDiff(diff),
      '.lvalue-percentage-slot': this.formatPercentage(model.get('percentage'))
    });

    if (diff < 0) {
      $changeEl.removeClass('good-diff').addClass('bad-diff');
    } else if (diff > 0) {
      $changeEl.removeClass('bad-diff').addClass('good-diff');
    } else {
      $changeEl.removeClass('bad-diff').removeClass('good-diff');
    }
  }
});
