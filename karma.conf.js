require('js-yaml');

module.exports = function(config) {
  var paths = require('./js_paths.yml');

  config.set({
    files: [].concat(
      paths.vendor.css.dest,
      paths.diamondash.css.dest,
      paths.vendor.js.src,
      paths.diamondash.jst.dest,
      paths.tests.jst.dest,
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
