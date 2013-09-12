diamondash.widgets.lvalue = function() {
  var widgets = diamondash.widgets;

  var LValueModel = widgets.widget.WidgetModel.extend({
    isStatic: false
  });

  var LastValueView = Backbone.View.extend({
    fadeDuration: 200,

    initialize: function(options) {
      this.widget = options.widget;
    },

    format: {
      short: d3.format(".2s"),
      long: d3.format(",f")
    },

    blink: function(fn) {
      this.$el.fadeOut(this.fadeDuration, function() {
        fn.call(this);
        this.$el.fadeIn(this.fadeDuration);
      }.bind(this));
    },

    render: function(longMode) {
      this.blink(function() {
        if (longMode) {
          this.$el
            .addClass('long')
            .removeClass('short')
            .text(this.format.long(this.model.get('last')));
        } else {
          this.$el
            .addClass('short')
            .removeClass('long')
            .text(this.format.short(this.model.get('last')));
        }
      });
    }
  });

  var LValueView = widgets.widget.WidgetView.extend({
    jst: _.template([
      '<h1 class="last"></h1>',
      '<div class="<%= change %> change">',
        '<span class="diff"><%= diff %></span> ',
        '<span class="percentage">(<%= percentage %>)</span>',
      '</div>',
      '<div class="time">',
        '<span class="from">from <%= from %></span>',
        '<span class="to">to <%= to %><span>',
      '</div>'
    ].join('')),
   
    initialize: function(options) {
      this.listenTo(this.model, 'change', this.render);

      this.last = new LastValueView({
        widget: this,
        model: this.model
      });

      this.mouseIsOver = false;
    },

    format: {
      diff: d3.format("+.3s"),
      percentage: d3.format(".2%"),

      _time: d3.time.format.utc("%d-%m-%Y %H:%M"),
      time: function(t) { return this._time(new Date(t)); },
    },

    render: function() {
      var model = this.model,
          last = model.get('last'),
          prev = model.get('prev'),
          diff = last - prev;

      var change;
      if (diff > 0) { change = 'good'; }
      else if (diff < 0) { change = 'bad'; }
      else { change = 'no'; }

      this.$('.widget-container').html(this.jst({
        from: this.format.time(model.get('from')),
        to: this.format.time(model.get('to')),
        diff: this.format.diff(diff),
        change: change,
        percentage: this.format.percentage(diff / (prev || 1))
      }));

      this.last
        .setElement(this.$('.last'))
        .render(this.mouseIsOver);
    },

    events: {
      'mouseenter': function() {
        this.mouseIsOver = true;
        this.last.render(true);
      },

      'mouseleave': function() {
        this.mouseIsOver = false;
        this.last.render(false);
      }
    }
  });

  return {
    LValueModel: LValueModel,
    LastValueView: LastValueView,
    LValueView: LValueView 
  };
}.call(this);
