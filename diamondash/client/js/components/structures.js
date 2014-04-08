diamondash.components.structures = function() {
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
    keyOf: function(view) {
      return _(view).result('id');
    },

    ensureKey: function(obj) {
      return obj instanceof Backbone.View
        ? this.keyOf(obj)
        : obj;
    },

    get: function(key) {
      return this.findByCustom(key);
    },

    make: function(options) {
      return new Backbone.View(options);
    },

    ensure: function(obj) {
      return !(obj instanceof Backbone.View)
        ? this.make(obj)
        : obj;
    },

    add: function(obj, key) {
      var view = this.ensure(obj);
      if (typeof key == 'undefined') { key = this.keyOf(view); }
      return ViewSet.__super__.add.call(this, view, key);
    },

    remove: function(obj) {
      var view = this.get(this.ensureKey(obj));
      if (view) { ViewSet.__super__.remove.call(this, view); }
      return this;
    },

    each: function(fn, that) {
      that = that || this;

      for (var k in this._indexByCustom) {
        fn.call(that, this.get(k), k);
      }
    }
  });

  ViewSet.extend = Extendable.extend;

  var SubviewSet = ViewSet.extend({
    parentAlias: 'parent',

    constructor: function(options) {
      SubviewSet.__super__.constructor.call(this);

      this.parent = options[this.parentAlias];
      this[this.parentAlias] = this.parent;
    },

    selector: function(key) {
      return key;
    },

    render: function() {
      this.each(function(view, key) {
        view.setElement(this.parent.$(this.selector(key)), true);
      }, this);

      this.apply('render', arguments);
    }
  });

  return {
    Extendable: Extendable,
    Eventable: Eventable,
    Registry: Registry,
    ColorMaker: ColorMaker,
    ViewSet: ViewSet,
    SubviewSet: SubviewSet
  };
}.call(this);
