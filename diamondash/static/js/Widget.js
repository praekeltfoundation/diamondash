/*
 * Abstract class for diamondash widgets
 */

Function.prototype.subclass = function(base) {
    var cls = Function.prototype.subclass.nonconstructor;
    cls.prototype = base.prototype;
    this.prototype = new cls();
};
Function.prototype.subclass.nonconstructor = function() {};

function Widget(args) {
	this.name = args.name;
	this.config = args.config;
	this.element = args.element;
}

Widget.prototype.initialize = function() {
	throw "initialize() cannot be called from abstract class Widget";
};

Widget.prototype.update = function(results) {
	throw "update() cannot be called from abstract class Widget";
};
