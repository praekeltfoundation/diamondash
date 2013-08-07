var widgets = diamondash.widgets;

widgets.LValueWidgetModel = widgets.WidgetModel.extend({
  isStatic: false
});

widgets.LValueWidgetView = widgets.WidgetView.extend({
  jst: _.template([
    '<h1 class="value"><%= value %></h1>',
    '<div class="<%= change %> change">',
      '<div class="diff"><%= diff %></div>',
      '<div class="percentage"><%= percentage %></div>',
    '</div>',
    '<div class="time">',
      '<div class="from">from <%= from %></div>',
      '<div class="to">to <%= to %><div>',
    '</div>'
  ].join('')),
 
  initialize: function(options) {
    this.listenTo(this.model, 'change', this.render);
  },

  formatLValue: d3.format(".2s"),
  formatDiff: d3.format("+.3s"),
  formatPercentage: d3.format(".2%"),

  _formatTime: d3.time.format.utc("%d-%m-%Y %H:%M"),
  formatTime: function(t) { return this._formatTime(new Date(t)); },

  render: function() {
    var model = this.model,
        diff = model.get('diff'),
        change;

    if (diff > 0) { change = 'good'; }
    else if (diff < 0) { change = 'bad'; }
    else { change = 'no'; }

    this.$el.html(this.jst({
      from: this.formatTime(model.get('from')),
      to: this.formatTime(model.get('to')),
      value: this.formatLValue(model.get('lvalue')),
      diff: this.formatDiff(diff),
      percentage: this.formatPercentage(model.get('percentage')),
      change: change
    }));
  }
});
