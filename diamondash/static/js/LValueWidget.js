var GOOD_COLOR = '#33cc33';
var BAD_COLOR = '#cc3333';

/*
 * Class for the diamondash lvalue widget
 */

function LValueWidget(args) {
	Widget.call(this, args);
	this.initialize();
}
LValueWidget.subclass(Widget);

LValueWidget.prototype = {
	initialize: function() {
		this.lvalueElement = this.element.querySelector('.lvalue-lvalue');
		this.timeElement = this.element.querySelector('.lvalue-time');
		this.diffElement = this.element.querySelector('.lvalue-diff');
		this.percentageElement = this.element.querySelector('.lvalue-percentage');
	},

	update: function(results) {
		this.lvalueElement.innerHTML = results.lvalue;
		this.timeElement.innerHTML = "since " + results.time;
		this.diffElement.innerHTML = results.diff;
		this.percentageElement.innerHTML = results.percentage;

		color = (results.diff > 0 
				? GOOD_COLOR
				: BAD_COLOR);
		this.diffElement.style.color = color;
		this.percentageElement.style.color = color;
	}
};
