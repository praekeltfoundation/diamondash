var widget = require("widgets/widget/widget");

module.exports = {
  LValueWidgetModel: widget.WidgetModel.extend({
    isStatic: false
  }),

  LValueWidgetView: widget.WidgetView.extend({
    initialize: function(options) {
      this.model.on('change', this.render, this);
    },

    bindings: [{
      el: '.lvalue-lvalue',
      attr: 'lvalue' 
    }, {
      el: '.lvalue-diff',
      attr: 'diff'
    }, {
      el: '.lvalue-percentage',
      attr: 'percentage',
      template: function(attr) { return "(" + attr + ")"; }
    }, {
      el: '.lvalue-from',
      attr: 'from',
      template: function(attr) { return "from " + attr; }
    }, {
      el: '.lvalue-to',
      attr: 'to',
      template: function(attr) { return "to " + attr; }
    }],

    render: function() {
      var $el = this.$el,
      model = this.model,
      bindings = this.bindings,
      i = -1,
      b, template, attr, text,
      diff, diffEl;

      // bind model data to view elements
      while (++i < bindings.length) {
        b = bindings[i];
        template = b.template;
        attr = model.get(b.attr);
        text = !template ? attr : template(attr);
        $el.find(b.el).text(text);
      }

      diff = Number(model.get('diff'));
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
