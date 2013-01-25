var assert = require('assert'),
lvalueWidget = require('../lvalue-widget'),
LValueWidgetModel = lvalueWidget.LValueWidgetModel,
LValueWidgetView = lvalueWidget.LValueWidgetView;

describe("LValueWidgetView", function(){
  describe(".render()", function() {
    it("should perform the correct mode-view attr-el mappings", function() {
      var StubbedLValueWidgetView,
      model, view,
      bindingResults, currentEl;

      StubbedLValueWidgetView = LValueWidgetView.extend({
        mappings: [
          {el: 'el1', attr: 'attr1'},
          {el: 'el2', attr: 'attr2'},
          {
            el: 'el3',
            attr: 'attr3',
            template: function(attr) {
              return "Hello, Mr. " + attr + ".";
            }
          }
        ]
      });

      model = new LValueWidgetModel({name: 'some-lvalue-widget'});
      view = new StubbedLValueWidgetView({
        model: model
      });

      bindingResults = {};
      view.$el.find = function(el) { 
        currentEl = el;

        return {
          text: function(text) { bindingResults[currentEl] = text; },
          addClass: function() { return this; },
          removeClass: function() { return this; }
        };
      };

      model.set({attr1: 'Laser', attr2: 'Blazer', attr3: 'Michelle'});
      view.render();

      assert.deepEqual(bindingResults, {
        'el1': "Laser",
        'el2': "Blazer",
        'el3': "Hello, Mr. Michelle."
      });
    });
  });
});
