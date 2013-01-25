var d3 = require('d3'),
    widget = require("widgets/widget/widget");

module.exports = {
  LValueWidgetModel: widget.WidgetModel.extend({
    isStatic: false
  }),

  LValueWidgetView: widget.WidgetView.extend({
    initialize: function(options) {
      this.model.on('change', this.render, this);
    },

    _formatTime: d3.time.format("%d-%m-%Y %H:%M"),
    formatTime: function(t) { return this._formatTime(new Date(t * 1000)); },

    mappings: [{
      el: '.lvalue-lvalue',
      attr: 'lvalue',
      format: d3.format(".1s")
    }, {
      el: '.lvalue-diff',
      attr: 'diff',
      format: d3.format(".3s")
    }, {
      el: '.lvalue-percentage',
      attr: 'percentage',
      template: function(attr) { return "(" + attr + ")"; },
      format: d3.format(".0%")
    }, {
      el: '.lvalue-from',
      attr: 'from',
      template: function(attr) { return "from " + attr; },
      format: 'formatTime'
    }, {
      el: '.lvalue-to',
      attr: 'to',
      template: function(attr) { return "to " + attr; },
      format: 'formatTime'
    }],

    render: function() {
      var $el = this.$el,
      model = this.model,
      mappings = this.mappings,
      i = -1,
      m, template, attr, format, text,
      diff, diffEl;

      // bind model data to view elements
      while (++i < mappings.length) {
        m = mappings[i];
        template = m.template;
        attr = model.get(m.attr);

        format = m.format;
        if (typeof format === "string") {
          attr = this[format](attr);
        } else if (typeof format === "function") {
          attr = format(attr);
        }

        text = !template ? attr : template(attr);
        $el.find(m.el).text(text);
      }

      diff = model.get('diff');
      diffEl = $el.find('.lvalue-change');
      if (diff < 0) {
        diffEl
          .removeClass('good-diff')
          .addClass('bad-diff');
      } else {
        diffEl
          .removeClass('bad-diff')
          .addClass('good-diff');
      }
    }
  })
};
