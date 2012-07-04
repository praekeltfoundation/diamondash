var DEFAULT_REQUEST_INTERVAL = 2000
var DEFAULT_GRAPH_COLOUR = '#0051cc'

var graphs = [];
var requestInterval = (config.requestInterval === undefined) ? DEFAULT_REQUEST_INTERVAL : config.requestInterval;

// construct the widget objects using the config
function constructWidgets() {
	graphElements = document.querySelectorAll('.graph'); 
    for (i = 0; i < graphElements.length; i++) {
		widgetName = $.trim(graphElements[i].id);
		widgetConfig = config.widgets[widgetName];

		graphs[i] = {
			name: widgetName,
			data: {},
			object: undefined
		};

		j = 0;
		metricSeries = [];
		for (metricName in widgetConfig.metrics) {
			metric = widgetConfig.metrics[metricName];

			graphs[i].data[metricName] = [{ x:0, y:0 }];
			metricColor = (metric.color === undefined) ? DEFAULT_GRAPH_COLOUR : metric.color;
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
		url = constructUrl(graph.name);
		getData(url, 
		function(results) {
			for (metricName in results) {
				resultMetricData = results[metricName];
				graphMetricData = graph.data[metricName];
				for (j = 0; j < resultMetricData.length; j++) {
					graphMetricData[j] = resultMetricData[j];
				}
				graph.data[metricName] = graphMetricData;
			}

			if (graph.name == 'multiple-metrics')
				console.log(graph.data);
			graph.object.update();
			metricData = null;
		});
	});

	$.each(graphs, function(i, graph) { 
		graph.object.update();
	});
}

// retrieve the data from the server
function getData(currentUrl, cbDataReceived) {
	obtainedData = [];
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
