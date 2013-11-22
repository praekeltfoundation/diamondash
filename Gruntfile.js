require('js-yaml');

module.exports = function(grunt) {
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-jst');
  grunt.loadNpmTasks('grunt-contrib-less');
  grunt.loadNpmTasks('grunt-exec');
  grunt.loadNpmTasks('grunt-karma');

  grunt.initConfig({
    paths: require('./js_paths.yml'),
    concat: {
      'vendor.css': {
        src: ['<%= paths.vendor.css.src %>'],
        dest: '<%= paths.vendor.css.dest %>'
      },
      'widgets.less': {
        src: ['<%= paths.diamondash.css.widgets.src %>'],
        dest: '<%= paths.diamondash.css.widgets.dest %>'
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
    less: {
      'diamondash.css': {
        options: {
          paths: ['<%= paths.diamondash.css.paths %>']
        },
        files: {
          '<%= paths.diamondash.css.dest %>':
            '<%= paths.diamondash.css.entry %>'
        }
      }
    },
    watch: {
      'vendor.css': {
        files: ['<%= paths.vendor.css.src %>'],
        tasks: ['concat:vendor.css']
      },
      'diamondash.css': {
        files: ['<%= paths.diamondash.css.src %>'],
        tasks: ['build:css']
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
      'diamondash.js.cleanup': {
        cmd: 'rm <%= paths.diamondash.js.cleanup.join(" ") %>'
      },
      'diamondash.css.cleanup': {
        cmd: 'rm <%= paths.diamondash.css.cleanup.join(" ") %>'
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
            '<%= paths.tests.jst.src %>']
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

  grunt.registerTask('build:vendor.js', [
    'concat:vendor.js',
  ]);

  grunt.registerTask('build:diamondash.js', [
    'jst:diamondash.jst',
    'concat:diamondash.js',
    'exec:diamondash.js.cleanup'
  ]);

  grunt.registerTask('build:vendor.css', [
    'concat:vendor.css',
  ]);

  grunt.registerTask('build:diamondash.css', [
    'concat:widgets.less',
    'less:diamondash.css',
    'exec:diamondash.css.cleanup',
  ]);

  grunt.registerTask('build:vendor.fonts', [
    'exec:vendor.fonts'
  ]);

  grunt.registerTask('build', [
    'build:vendor.css',
    'build:vendor.js',
    'build:vendor.fonts',
    'build:diamondash.css',
    'build:diamondash.js'
  ]);

  grunt.registerTask('default', [
    'build',
    'test'
  ]);

  grunt.registerTask('test', [
    'jst:diamondash.jst',
    'build:diamondash.css',
    'karma',
    'exec:tests.cleanup'
  ]);
};
