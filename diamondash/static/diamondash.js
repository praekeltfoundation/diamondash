var DEFAULT_REQUEST_INTERVAL = 2000
var DEFAULT_GRAPH_COLOUR = '#3333cc'

var graphs = [];
var requestInterval = config.requestInterval || DEFAULT_REQUEST_INTERVAL;

function Hover(graphObject, widgetMetricsConfig, legend) {
	var HoverDetail = Rickshaw.Class.create(Rickshaw.Graph.HoverDetail, {
		render: function(args) {
			var timeLabel = legend.querySelector('.graph-time-label');
			timeLabel.innerHTML = args.formattedXValue;

			// for each metric
			args.detail.sort(function(a, b) { return a.order - b.order }).forEach(function(d) {
				var title = widgetMetricsConfig[d.name].title;
				var key = legend.querySelector('#metric-key-container-' + d.name);
				var label = key.querySelector('#metric-key-label-' + d.name);
				label.innerHTML = title + ": " + d.formattedYValue;

				var dot = document.createElement('div');
				dot.className = 'dot';
				dot.style.top = graphObject.y(d.value.y0 + d.value.y) + 'px';
				dot.style.borderColor = d.series.color;

				this.element.appendChild(dot);
				dot.className = 'dot active';

				this.show()
			}, this);
		}
	});

	return new HoverDetail({graph: graphObject});
}

function constructMetricKey(legend, metricName, metricTitle, metricColor) {
	var metricKey = document.createElement('div');
	metricKey.id = 'metric-key-container-'+metricName;
	metricKey.className = 'metric-key-container';

	var swatch = document.createElement('div');
	swatch.className = 'metric-key-swatch';
	swatch.id = 'metric-key-swatch-'+metricName;
	swatch.style.backgroundColor = metricColor;

	var label = document.createElement('div');
	label.className = 'metric-key-label';
	label.id = 'metric-key-label-'+metricName;
	label.innerHTML = metricTitle;

	metricKey.appendChild(swatch);
	metricKey.appendChild(label);
	legend.appendChild(metricKey);
}

// construct the widget objects using the config
function constructWidgets() {
	var graphWidgets = document.querySelectorAll('.graph-widget'); 
    for (var i = 0; i < graphWidgets.length; i++) {
		var widgetElement = graphWidgets[i];
		var legend = widgetElement.querySelector('.legend');
		var widgetName = $.trim(widgetElement.id);
		var widgetConfig = config.widgets[widgetName];
		var graphObject = null;
		var graphData = {};

		// build the structures needed for each metric
		var j = 0;
		var metricSeries = [];
		for (var metricName in widgetConfig.metrics) {
			var metric = widgetConfig.metrics[metricName];

			graphData[metricName] = [{ x:0, y:0 }];
			var metricColor = metric.color || DEFAULT_GRAPH_COLOUR;
			metricSeries[j] = {
				data: graphData[metricName],
				color: metricColor,
				name: metricName
			}

			constructMetricKey(legend, metricName, metric.title, metricColor);

			j++;
		}

		graphObject = new Rickshaw.Graph({
			element: widgetElement.querySelector('.graph'),
			renderer: 'line',
			series: metricSeries
		});
		
		var xAxis = new Rickshaw.Graph.Axis.Time({
			graph: graphObject 
		});

		var yAxis = new Rickshaw.Graph.Axis.Y({
			element: widgetElement.querySelector('.y-axis'),
			orientation: 'left',
			graph: graphObject,
			tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
		});

		var hover = new Hover(graphObject, widgetConfig.metrics, legend);

		graphObject.render();

		graphs[i] = {
			name: widgetName,
			data: graphData,
			object: graphObject
		};
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
