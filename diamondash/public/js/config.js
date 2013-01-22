var vendorPath = "/public/vendor/";

require.config({
  baseUrl: '/public/js/',

  paths: {
    'jquery': vendorPath + "jquery",
    'underscore': vendorPath + "underscore",
    'backbone': vendorPath + "backbone",
    'd3': vendorPath + "d3.v2"
  },

  shim: {
    'backbone': {
      deps: ['underscore', 'jquery'],
      exports: 'Backbone'
    }
  }
});


// TODO I cannot find away around this right now
require(['jquery', 'backbone'], function($, Backbone) { Backbone.$ = $; });
