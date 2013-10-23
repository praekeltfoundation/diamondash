window.diamondash = function() {
  var DiamondashConfigModel = Backbone.RelationalModel.extend({
    defaults: {
      url_prefix: ''
    }
  });

  var config = new DiamondashConfigModel();

  function url() {
    var parts = _(arguments).toArray();
    parts.unshift(config.get('url_prefix'));
    parts.unshift('/');
    return diamondash.utils.joinPaths.apply(this, parts);
  }

  return {
    url: url,
    config: config
  };
}.call(this);
