window.diamondash = function() {
  function url() {
    var parts = _(arguments).toArray();
    parts.unshift(diamondash.config.get('url_prefix'));
    parts.unshift('/');
    return diamondash.utils.joinPaths.apply(this, parts);
  }

  return {
    url: url
  };
}.call(this);
