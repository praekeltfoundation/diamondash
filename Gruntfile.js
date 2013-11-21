require('js-yaml');

module.exports = function(grunt) {
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-jst');
  grunt.loadNpmTasks('grunt-exec');
  grunt.loadNpmTasks('grunt-karma');

  grunt.initConfig({
    paths: require('./js_paths.yml'),
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
        src: [
          '<%= paths.diamondash.jst.dest %>',
          '<%= paths.diamondash.js.src %>'],
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
      },
      'diamondash.jst': {
        files: ['<%= paths.diamondash.jst.src %>'],
        tasks: ['jst:diamondash.jst']
      }
    },
    exec: {
      'vendor.fonts': {
        cmd: 'cp <%= paths.vendor.fonts.src %> <%= paths.vendor.fonts.dest %>'
      },
      'tests.cleanup': {
        cmd: 'rm <%= paths.tests.cleanup %>'
      },
      'diamondash.cleanup': {
        cmd: 'rm <%= paths.diamondash.cleanup %>'
      }
    },
    jst: {
      'diamondash.jst': {
        files: {
          '<%= paths.diamondash.jst.dest %>': [
            '<%= paths.diamondash.jst.src %>'
          ]
        }
      },
      'test-templates.jst': {
        files: {
          '<%= paths.tests.jst.dest %>': [
            '<%= paths.tests.jst.src %>'
          ]
        }
      },
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
    'jst:diamondash.jst',
    'exec:vendor.fonts',
    'concat',
    'exec:diamondash.cleanup'
  ]);

  grunt.registerTask('default', [
    'build',
    'test'
  ]);

  grunt.registerTask('test', [
    'jst:diamondash.jst',
    'karma',
    'exec:tests.cleanup'
  ]);
};
