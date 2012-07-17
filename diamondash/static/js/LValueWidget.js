/*
 * Class for the diamondash lvalue widget
 */

var GOOD_COLOR = '#33cc33';
var BAD_COLOR = '#cc3333';

function LValueWidget(args) {
	Widget.call(this, args);
	this.initialize();
}
LValueWidget.subclass(Widget);

LValueWidget.prototype.initialize = function() {
	this.lvalueElement = this.element.querySelector('.lvalue-lvalue');
	this.fromElement = this.element.querySelector('.lvalue-from');
	this.toElement = this.element.querySelector('.lvalue-to');
	this.diffElement = this.element.querySelector('.lvalue-diff');
	this.percentageElement = this.element.querySelector('.lvalue-percentage');
};

LValueWidget.prototype.update = function(results) {
	this.lvalueElement.innerHTML = results.lvalue;
	this.fromElement.innerHTML = "from " + results.from;
	this.toElement.innerHTML = "to " + results.to;
	this.diffElement.innerHTML = results.diff;
	this.percentageElement.innerHTML = "(" + results.percentage + ")";

	color = (results.diff >= 0 
			? GOOD_COLOR
			: BAD_COLOR);
	this.diffElement.style.color = color;
	this.percentageElement.style.color = color;
};
