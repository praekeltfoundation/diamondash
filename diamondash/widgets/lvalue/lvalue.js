diamondash.widgets.lvalue = function() {
  var widgets = diamondash.widgets,
      dynamic = diamondash.widgets.dynamic,
      widget = diamondash.widgets.widget;

  var LValueModel = dynamic.DynamicWidgetModel.extend({
    valueIsBad: function(v) {
      return v !== 0 && !v;
    },

    validate: function(attrs, options) {
      if (this.valueIsBad(attrs.last)) {
        return "LValueModel has bad 'last' attr: " + attrs.last;
      }

      if (this.valueIsBad(attrs.prev)) {
        return "LValueModel has bad 'prev' attr: " + attrs.prev;
      }

      if (this.valueIsBad(attrs.from)) {
        return "LValueModel has bad 'from' attr: " + attrs.from;
      }

      if (this.valueIsBad(attrs.to)) {
        return "LValueModel has bad 'to' attr: " + attrs.to;
      }
    }
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
      var self = this;

      this.$el.fadeOut(this.fadeDuration, function() {
        fn.call(self);
        self.$el.fadeIn(self.fadeDuration);
      });
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

  var LValueView = widget.WidgetView.extend({
    jst: JST['diamondash/widgets/lvalue/lvalue.jst'],
   
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
      if (this.model.isValid()) {
        var last = this.model.get('last');
        var prev = this.model.get('prev');
        var diff = last - prev;

        var change;
        if (diff > 0) { change = 'good'; }
        else if (diff < 0) { change = 'bad'; }
        else { change = 'no'; }

        this.$el.html(this.jst({
          from: this.format.time(this.model.get('from')),
          to: this.format.time(this.model.get('to')),
          diff: this.format.diff(diff),
          change: change,
          percentage: this.format.percentage(diff / (prev || 1))
        }));

        this.last
          .setElement(this.$('.last'))
          .render(this.mouseIsOver);
      }

      return this;
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

  widgets.registry.models.add('lvalue', LValueModel);
  widgets.registry.views.add('lvalue', LValueView);

  return {
    LValueModel: LValueModel,
    LastValueView: LastValueView,
    LValueView: LValueView 
  };
}.call(this);
