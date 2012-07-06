var DEFAULT_REQUEST_INTERVAL = 2000
var DEFAULT_GRAPH_COLOUR = '#0051cc'

var graphs = [];
var requestInterval = config.requestInterval || DEFAULT_REQUEST_INTERVAL;

// construct the widget objects using the config
function constructWidgets() {
	var graphElements = document.querySelectorAll('.graph'); 
    for (var i = 0; i < graphElements.length; i++) {
		var widgetName = $.trim(graphElements[i].id);
		var widgetConfig = config.widgets[widgetName];

		graphs[i] = {
			name: widgetName,
			data: {},
			object: undefined
		};

		var j = 0;
		var metricSeries = [];
		for (var metricName in widgetConfig.metrics) {
			var metric = widgetConfig.metrics[metricName];

			graphs[i].data[metricName] = [{ x:0, y:0 }];
			var metricColor = metric.color || DEFAULT_GRAPH_COLOUR;
			metricSeries[j] = {
				data: graphs[i].data[metricName],
				color: metricColor
			}

			j++;
		}
		
		graphs[i].object = new Rickshaw.Graph({
			element: graphElements[i],
			renderer: 'line',
			series: metricSeries
		});

		graphs[i].object.render();
	}
}

// construct the url to be sent as a request to the server
function constructUrl(widgetName) {
	return '/render/' + config.dashboardName + '/' + widgetName;
}

// called each update interval
function updateWidgets() {
	$.each(graphs, function(i, graph) { 
		var url = constructUrl(graph.name);
		getData(url, 
		function(results) {
			for (var metricName in results) {
				var resultMetricData = results[metricName];
				var graphMetricData = graph.data[metricName];

				for (var j = 0; j < resultMetricData.length; j++) {
					graphMetricData[j] = resultMetricData[j];
				}
			}
			graph.object.update();
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
