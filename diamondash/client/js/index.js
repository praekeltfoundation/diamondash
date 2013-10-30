window.diamondash = function() {
  var DiamondashConfigModel = Backbone.RelationalModel.extend({
    relations: [{
      type: Backbone.HasOne,
      key: 'auth',
      relatedModel: 'diamondash.models.AuthModel',
      includeInJSON: false
    }],

    defaults: {
      auth: {}
    }
  });

  function url() {
    var parts = _(arguments).toArray();
    parts.unshift(diamondash.config.get('url_prefix'));
    parts.unshift('/');
    return diamondash.utils.joinPaths.apply(this, parts);
  }

  return {
    url: url,
    DiamondashConfigModel: DiamondashConfigModel
  };
}.call(this);
