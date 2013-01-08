var vendorPath = "../vendor/";

require.config({
	baseUrl: 'public/js',
	paths: {
		'backbone': vendorPath + "backbone",
		'underscore': vendorPath + "underscore"
	},
	shim: {
		'backbone': {exports: 'backbone'},
		'underscore': {exports: '_'}
	}
});

require(['widget'], function(widget) {
	var m = new widget.WidgetModel();
	console.log(m.doNothing());
});
