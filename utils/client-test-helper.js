assert = require('assert');
sinon = require('sinon');


document = require("jsdom").jsdom("<html><head></head><body></body></html>");
window = document.createWindow();
navigator = window.navigator;

$ = require('jquery');
_ = require('../diamondash/client/vendor/underscore');
Backbone = require('../diamondash/client/vendor/backbone');
Backbone.$ = $;

window = global;
require('../diamondash/public/js/diamondash');
