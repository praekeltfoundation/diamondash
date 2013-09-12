assert = require('assert');
sinon = require('sinon');


document = require("jsdom").jsdom("<html><head></head><body></body></html>");
window = document.createWindow();
navigator = window.navigator;

$ = require('jquery');
_ = require('../vendor/underscore');
Backbone = require('../vendor/backbone');
Backbone.$ = $;

window = global;
require('../../public/js/vendor');
require('../../public/js/diamondash');
