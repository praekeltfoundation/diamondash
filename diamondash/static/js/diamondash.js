var DEFAULT_REQUEST_INTERVAL = 2000;

var widgets = [];
var requestInterval = config.request_interval || DEFAULT_REQUEST_INTERVAL;


// build the widget objects using the config
function buildWidgets() {
	var graphWidgets = document.querySelectorAll('.graph-widget'); 
	var i = 0;
    for (i = 0; i < graphWidgets.length; i++) {
		buildWidget(graphWidgets[i], GraphWidget);
	}

	var lvalueWidgets = document.querySelectorAll('.lvalue-widget'); 
    for (i = 0; i < lvalueWidgets.length; i++) {
		buildWidget(lvalueWidgets[i], LValueWidget);
	}
}

function buildWidget(widgetElement, WidgetType) {
	var widgetName = $.trim(widgetElement.id);
	var widgetConfig = config.widgets[widgetName];

	widgets.push(new WidgetType({
		name: widgetName,
		config: widgetConfig,
		element: widgetElement
	}));
}

// build the url to be sent as a request to the server
function buildUrl(widgetName) {
	return '/render/' + config.name + '/' + widgetName;
}

// called each update interval
function updateWidgets() {
	$.each(widgets, function(i, widget) { 
		var url = buildUrl(widget.name);
		getData(url, 
			function(results) {
				widget.update(results);
			});
	});
}

// retrieve the data from the server
function getData(currentUrl, cbDataReceived) {
	$.ajax({

		/*beforeSend: function(xhr) {
		  if (auth.length > 0) {
		  var bytes = Crypto.charenc.Binary.stringToBytes(auth);
		  var base64 = Crypto.util.bytesToBase64(bytes);
		  xhr.setRequestHeader("Authorization", "Basic " + base64);
		  }
		  },*/

		dataType: 'json',
	error: function(xhr, textStatus, errorThrown) {
		console.log("Error: " + xhr + " " + textStatus + " " + errorThrown);
	},
	url: currentUrl
	}).done(function(responseData) {
		// callback fired when the response data is received
		cbDataReceived(responseData);
	});
}

buildWidgets();
updateWidgets();

var updateId = setInterval(updateWidgets, requestInterval);
