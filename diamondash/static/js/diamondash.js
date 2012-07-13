var DEFAULT_REQUEST_INTERVAL = 2000;
var DEFAULT_GRAPH_COLOUR = '#3333cc';

var graphs = [];
var requestInterval = config.request_interval || DEFAULT_REQUEST_INTERVAL;


// construct the widget objects using the config
function constructWidgets() {
	var graphWidgets = document.querySelectorAll('.graph-widget'); 
	var i = 0;
    for (i = 0; i < graphWidgets.length; i++) {
		var widgetElement = graphWidgets[i];
		var widgetName = $.trim(widgetElement.id);
		var widgetConfig = config.widgets[widgetName];

		graphs[i] = new GraphWidget({
			name: widgetName,
			config: widgetConfig,
			element: widgetElement
		});
	}
}

// construct the url to be sent as a request to the server
function constructUrl(widgetName) {
	return '/render/' + config.name + '/' + widgetName;
}

// called each update interval
function updateWidgets() {
	$.each(graphs, function(i, graph) { 
		var url = constructUrl(graph.name);
		getData(url, 
		function(results) {
			graph.update(results);
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

constructWidgets();
updateWidgets();

var updateId = setInterval(updateWidgets, requestInterval);
