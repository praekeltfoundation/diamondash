diamondash.components.structures = function() {
  var utils = diamondash.utils;

  function Extendable() {}
  Extendable.extend = Backbone.Model.extend;

  var Eventable = Extendable.extend(Backbone.Events);

  var ColorMaker = Extendable.extend({
    constructor: function(options) {
      options = _({}).defaults(options, this.defaults);
      this.colors = options.scale.domain(d3.range(0, options.n));
      this.i = 0;
    },

    defaults: {
      scale: d3.scale.category10(),
      n: 10
    },

    next: function() {
      return this.colors(this.i++);
    }
  });

  Registry = Eventable.extend({
    constructor: function(items) {
      this.items = {};
      
      _(items || {}).each(function(data, name) {
        this.add(name, data);
      }, this);
    },

    processAdd: function(name, data) {
      return data;
    },

    processGet: function(name, data) {
      return data;
    },

    add: function(name, data) {
      if (name in this.items) {
        throw new Error("'" + name + "' is already registered.");
      }

      data = this.processAdd(name, data);
      this.trigger('add', name, data);
      this.items[name] = data;
    },

    get: function(name) {
      return this.processGet(name, this.items[name]);
    },

    remove: function(name) {
      var data = this.items[name];
      this.trigger('remove', name, data);
      delete this.items[name];
      return data;
    }
  });

  var ViewSet = Extendable.extend.call(Backbone.ChildViewContainer, {
    idOf: function(obj) {
      return _(obj).result('id');
    },

    ensureId: function(obj) {
      return obj instanceof Backbone.View
        ? this.idOf(obj)
        : obj;
    },

    get: function(id) {
      return this.findByCustom(id);
    },

    add: function(widget) {
      return ViewSet.__super__.add.call(this, widget, this.idOf(widget));
    },

    remove: function(obj) {
      var widget = this.get(this.ensureId(obj));
      if (widget) { ViewSet.__super__.remove.call(this, widget); }
      return this;
    }
  });

  ViewSet.extend = Extendable.extend;

  return {
    Extendable: Extendable,
    Eventable: Eventable,
    Registry: Registry,
    ColorMaker: ColorMaker,
    ViewSet: ViewSet
  };
}.call(this);
