diamondash.utils = function() {
  function objectByName(name, that) {
    return _(name.split( '.' )).reduce(
      function(obj, propName) { return obj[propName]; },
      that || this);
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

  return {
    functor: functor,
    objectByName: objectByName,
    bindEvents: bindEvents,
    snap: snap
  };
}.call(this);
