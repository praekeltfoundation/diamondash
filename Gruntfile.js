module.exports = function(grunt) {
  var globalStylesheets = [
    "diamondash/client/vendor/bootstrap/css/bootstrap.css",
    "diamondash/client/vendor/bootstrap/css/bootstrap-responsive.css",
    "diamondash/client/css/style.css"
  ];

  var indexStylesheets = [].concat(globalStylesheets, [
    "diamondash/client/css/index.css"
  ]);

  var errorStylesheets = [].concat(globalStylesheets, [
    "diamondash/client/css/error.css"
  ]);

  var dashboardStylesheets = [].concat(globalStylesheets, [
    "diamondash/client/css/dashboard.css",
    "diamondash/widgets/**/*.css"
  ]);

  var diamondashModules = [
    // vendor modules
    "diamondash/client/vendor/jquery.js",
    "diamondash/client/vendor/underscore.js",
    "diamondash/client/vendor/backbone.js",
    "diamondash/client/vendor/d3.js",

    "diamondash/client/js/index.js",
    "diamondash/widgets/index.js",
    "diamondash/widgets/widget/widget.js",
    "diamondash/widgets/graph/graph.js",
    "diamondash/widgets/lvalue/lvalue.js",
    "diamondash/client/js/dashboard.js",
  ];

  grunt.initConfig({
    concat: {
      "index.css": {
        src: indexStylesheets,
        dest: "diamondash/public/css/index.css"
      },
      "error.css": {
        src: errorStylesheets,
        dest: "diamondash/public/css/error.css"
      },
      "dashboard.css": {
        src: dashboardStylesheets,
        dest: "diamondash/public/css/dashboard.css"
      },
      "diamondash.js": {
        src: diamondashModules,
        dest: "diamondash/public/js/diamondash.js"
      }
    },
    watch: {
      "index.css": {
        files: indexStylesheets,
        tasks: ["concat:index.css"]
      },
      "error.css": {
        files: errorStylesheets,
        tasks: ["concat:error.css"]
      },
      "dashboard.css": {
        files: dashboardStylesheets,
        tasks: ["concat:dashboard.css"]
      },
      "diamondash.js": {
        files: diamondashModules,
        tasks: ["concat:diamondash.js"]
      }
    },
    mocha: {
      "diamondash.js": {
        tests: [
          "diamondash/client/**/*.test.js",
          "diamondash/widgets/**/*.test.js"
        ],
        requires: ["utils/client-test-helper.js"]
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
