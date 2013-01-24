var vendorPath = "/public/vendor/";

require.config({
  baseUrl: '/public/js/',

  paths: {
    'jquery': vendorPath + "jquery",
    'underscore': vendorPath + "underscore",
    'backbone': vendorPath + "backbone",
    'd3': vendorPath + "d3"
  },

  shim: {
    'd3': {exports: 'd3'},
    'backbone': {
      deps: ['underscore', 'jquery'],
      exports: 'Backbone'
    }
  }
});


require(['jquery', 'backbone'], function($, Backbone) {
  Backbone.$ = $;
});
