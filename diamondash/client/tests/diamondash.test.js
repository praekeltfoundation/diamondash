describe.only("diamondash", function() {
  describe(".url()", function() {
    before(function() {
      diamondash.config.set('url_prefix', 'foo');
    });

    after(function() {
      diamondash.config.set(
        'url_prefix',
        diamondash.config.previous('url_prefix'));
    });

    it("should construct a url with the configured prefix", function() {
      assert.equal(diamondash.url('a', 'b', 'c'), '/foo/a/b/c');
    });
  });
});
