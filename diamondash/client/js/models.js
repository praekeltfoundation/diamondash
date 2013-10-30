diamondash.models = function() {
  var AuthModel = Backbone.RelationalModel.extend({
    defaults: {
      all: false
    },

    stringify: function() {
      return diamondash.utils.basicAuth(
        this.get('username'),
        this.get('password'));
    }
  });

  return {
    AuthModel: AuthModel
  };
}.call(this);
