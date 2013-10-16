diamondash.utils = function() {
  function objectByName(name, that) {
    return _(name.split( '.' )).reduce(
      function(obj, propName) { return obj[propName]; },
      that || this);
  }

  function maybeByName(obj, that) {
    return _.isString(obj)
      ? objectByName(obj, that)
      : obj;
  }

  function functor(obj) {
    return !_.isFunction(obj)
      ? function() { return obj; }
      : obj;
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

  function snap(x, start, step) {
    var i = Math.round((x - start) / step);
    return start + (step * i);
  }

  function d3Map(selection, fn) {
    var values = [];

    selection.each(function(d, i) {
      values.push(fn.call(this, d, i));
    });

    return values;
  }

  function extend(superConstructor, proto, statics) {
    return Backbone.Model.extend.call(superConstructor, proto, statics);
  }

  return {
    functor: functor,
    objectByName: objectByName,
    maybeByName: maybeByName,
    bindEvents: bindEvents,
    snap: snap,
    d3Map: d3Map,
    extend: extend
  };
}.call(this);
