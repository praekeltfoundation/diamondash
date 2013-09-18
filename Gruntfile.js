require('js-yaml');

module.exports = function(grunt) {
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-exec');
  grunt.loadNpmTasks('grunt-karma');

  var paths = require('./js_paths.yml');

  grunt.initConfig({
    paths: paths,
    concat: {
      'vendor.css': {
        src: ['<%= paths.vendor.css.src %>'],
        dest: '<%= paths.vendor.css.dest %>'
      },
      'diamondash.css': {
        src: ['<%= paths.diamondash.css.src %>'],
      dest: '<%= paths.diamondash.css.dest %>'
      },
      'vendor.js': {
        src: ['<%= paths.vendor.js.src %>'],
        dest: '<%= paths.vendor.js.dest %>'
      },
      'diamondash.js': {
        src: ['<%= paths.diamondash.js.src %>'],
        dest: '<%= paths.diamondash.js.dest %>'
      }
    },
    watch: {
      'vendor.css': {
        files: ['<%= paths.vendor.css.src %>'],
        tasks: ['concat:vendor.css']
      },
      'diamondash.css': {
        files: ['<%= paths.diamondash.css.src %>'],
        tasks: ['concat:diamondash.css']
      },
      'vendor.js': {
        files: ['<%= paths.vendor.js.src %>'],
        tasks: ['concat:vendor.js']
      },
      'diamondash.js': {
        files: ['<%= paths.diamondash.js.src %>'],
        tasks: ['concat:diamondash.js']
      }
    },
    exec: {
      'vendor.fonts': {
        cmd: 'cp <%= paths.vendor.fonts.src %> <%= paths.vendor.fonts.dest %>'
      }
    },
    karma: {
      dev: {
        singleRun: true,
        reporters: ['dots'],
        configFile: 'karma.conf.js'
      }
    }
  });

  grunt.registerTask('build', [
    'exec:vendor.fonts',
    'concat'
  ]);

  grunt.registerTask('default', [
    'build',
    'test'
  ]);

  grunt.registerTask('test', [
    'karma'
  ]);
};
