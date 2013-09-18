require('js-yaml');

module.exports = function(config) {
  var paths = require('./js_paths.yml');

  config.set({
    files: [].concat(
      paths.vendor.css.src,
      paths.diamondash.css.src,
      paths.vendor.js.src,
      paths.diamondash.js.src,
      paths.tests.vendor,
      paths.tests.spec
    ),

    browsers: ['PhantomJS'],
    frameworks: ['mocha'],

    plugins: [
      'karma-mocha',
      'karma-phantomjs-launcher'
    ]
  });
};
