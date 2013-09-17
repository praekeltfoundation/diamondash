require('js-yaml');

module.exports = function(grunt) {
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-karma');

  grunt.initConfig({
    paths: require('./js_paths.yml'),
    concat: {
      'vendor.css': {
        src: ['<%= paths.client.css.vendor.src %>'],
        dest: '<%= paths.client.css.vendor.dest %>'
      },
      'diamondash.css': {
        src: ['<%= paths.client.css.diamondash.src %>'],
      dest: '<%= paths.client.css.diamondash.dest %>'
      },
      'vendor.js': {
        src: ['<%= paths.client.js.vendor.src %>'],
        dest: '<%= paths.client.js.vendor.dest %>'
      },
      'diamondash.js': {
        src: ['<%= paths.client.js.diamondash.src %>'],
        dest: '<%= paths.client.js.diamondash.dest %>'
      }
    },
    watch: {
      'vendor.css': {
        files: ['<%= paths.client.css.vendor.src %>'],
        tasks: ['concat:vendor.css']
      },
      'diamondash.css': {
        files: ['<%= paths.client.css.diamondash.src %>'],
        tasks: ['concat:diamondash.css']
      },
      'vendor.js': {
        files: ['<%= paths.client.js.vendor.src %>'],
        tasks: ['concat:vendor.js']
      },
      'diamondash.js': {
        files: ['<%= paths.client.js.diamondash.src %>'],
        tasks: ['concat:diamondash.js']
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
