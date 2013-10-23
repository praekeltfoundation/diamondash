window.diamondash = function() {
  var DiamondashConfigModel = Backbone.RelationalModel.extend({
    defaults: {
      url_prefix: ''
    }
  });

  var config = new DiamondashConfigModel();

  return {
    config: config
  };
}.call(this);
