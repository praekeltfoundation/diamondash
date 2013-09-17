require('js-yaml');

module.exports = function(config) {
  var paths = require('./js_paths.yml');

  config.set({
    files: [].concat(
      paths.client.css.vendor.src,
      paths.client.css.diamondash.src,
      paths.client.js.vendor.src,
      paths.client.js.diamondash.src,
      paths.tests.client.vendor,
      paths.tests.client.spec
    ),

    browsers: ['PhantomJS'],
    frameworks: ['mocha'],

    plugins: [
      'karma-mocha',
      'karma-phantomjs-launcher'
    ]
  });
};
