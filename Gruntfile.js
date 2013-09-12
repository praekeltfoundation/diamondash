require('js-yaml');

module.exports = function(grunt) {
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
        tasks: ["concat:vendor.css"]
      },
      'diamondash.css': {
        files: ['<%= paths.client.css.diamondash.src %>'],
        tasks: ["concat:diamondash.css"]
      },
      'vendor.js': {
        files: ['<%= paths.client.js.vendor.src %>'],
        tasks: ["concat:vendor.js"]
      },
      'diamondash.js': {
        files: ['<%= paths.client.js.diamondash.src %>'],
        tasks: ["concat:diamondash.js"]
      }
    },
    mocha: {
      client: {
        tests: ['<%= paths.tests.client.spec %>'],
        requires: ['diamondash/client/tests/init.js']
      }
    }
  });

  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-watch');

  grunt.registerTask("default", ["concat"]);
  grunt.registerTask("test", ["mocha"]);

  grunt.registerMultiTask("mocha", "Mocha", function () {
    var exec = require('child_process').exec,
        callback = this.async(),
        requires,
        tests,
        cmd;

      requires = grunt.file.expand(this.data.requires || []).map(
        function(file) { return "--require " + file; });

      tests = grunt.file.expand(this.data.tests || []);

      cmd = [].concat([
        "NODE_ENV=test",
        "./node_modules/mocha/bin/mocha",
        "--reporter", this.data.reporter || "spec",
        "--ui", this.data.ui || "bdd",
        "--colors"
      ], requires, tests).join(" ");

    exec(cmd, function(err, output) {
      if (err !== null) { throw(err); }
      console.log(output);
      callback();
    });
  });
};
