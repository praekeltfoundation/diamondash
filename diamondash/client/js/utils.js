diamondash.utils = function() {
  function objectByName(name, that) {
    return _(name.split( '.' )).reduce(
      function(obj, propName) { return obj[propName]; },
      that || this);
  }

  function bindEvents(events, that) {
    that = that || this;

    _(events).each(function(fn, e) {
      var parts = e.split(' '),
          event = parts[0],
          entity = parts[1];

      if (entity) { that.listenTo(objectByName(entity, that), event, fn); }
      else { that.on(event, fn); }
    });
  }

  function ColorMaker(options) {
    options = _({}).defaults(options, this.defaults);
    this.colors = options.scale.domain(d3.range(0, options.n));
    this.i = 0;
  }

  ColorMaker.prototype = {
    defaults: {
      scale: d3.scale.category10(),
      n: 10
    },

    next: function() {
      return this.colors(this.i++);
    }
  };

  return {
    objectByName: objectByName,
    bindEvents: bindEvents,
    ColorMaker: ColorMaker
  };
}.call(this);
