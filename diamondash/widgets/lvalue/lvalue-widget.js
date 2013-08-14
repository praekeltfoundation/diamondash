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

  format: {
    value: d3.format(".2s"),
    diff: d3.format("+.3s"),
    percentage: d3.format(".2%"),

    _time: d3.time.format.utc("%d-%m-%Y %H:%M"),
    time: function(t) { return this._time(new Date(t)); },
  },

  render: function() {
    var model = this.model,
        diff = model.get('diff'),
        change;

    if (diff > 0) { change = 'good'; }
    else if (diff < 0) { change = 'bad'; }
    else { change = 'no'; }

    this.$('.lvalue-widget-container').html(this.jst({
      from: this.format.time(model.get('from')),
      to: this.format.time(model.get('to')),
      value: this.format.value(model.get('lvalue')),
      diff: this.format.diff(diff),
      percentage: this.format.percentage(model.get('percentage')),
      change: change
    }));
  }
});
