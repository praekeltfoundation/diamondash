var DEFAULT_REQUEST_INTERVAL = 2000;
var DEFAULT_GRAPH_COLOUR = '#3333cc';

var graphs = [];
var requestInterval = config.requestInterval || DEFAULT_REQUEST_INTERVAL;

function Hover(graph, widgetMetricsConfig, legend, hoverLegend) {
	var HoverDetail = Rickshaw.Class.create(Rickshaw.Graph.HoverDetail, {
		render: function(args) {
			var hoverTimeLabel = hoverLegend.querySelector('.graph-time-label');
			hoverTimeLabel.innerHTML = args.formattedXValue;

			// for each metric
			args.detail.sort(
				function(a, b) { 
					return a.order - b.order;
				}).forEach(
				function(d) {
				var title = widgetMetricsConfig[d.name].title;
				var key = hoverLegend.querySelector('#metric-key-container-' + d.name);
				var label = key.querySelector('#metric-key-label-' + d.name);
				var valueLabel = key.querySelector('#metric-key-value-label-' + d.name);

				label.innerHTML = title + ": ";
				valueLabel.innerHTML = d.formattedYValue;

				var dot = document.createElement('div');
				dot.className = 'dot';
				dot.style.top = graph.object.y(d.value.y0 + d.value.y) + 'px';
				dot.style.borderColor = d.series.color;
				this.element.appendChild(dot);
				dot.className = 'dot active';

				this.show();
			}, this);
		},

		hide: function() {
			this.visible = false;
			this.element.classList.add('inactive');
			legend.classList.remove('inactive');
			hoverLegend.classList.add('inactive');

			if (typeof this.onHide === 'function') {
				this.onHide();
			}
		},

		show: function() {
			this.visible = true;
			this.element.classList.remove('inactive');
			legend.classList.add('inactive');
			hoverLegend.classList.remove('inactive');

			if (typeof this.onShow === 'function') {
				this.onShow();
			}
		}
	});

	return new HoverDetail({graph: graph.object});
}

// Construct the passed in metric's key in the legend
function constructMetricKey(legend, metricName, metricTitle, metricColor) {
	var metricKey = document.createElement('div');
	metricKey.id = 'metric-key-container-' + metricName;
	metricKey.className = 'metric-key-container';

	var swatch = document.createElement('div');
	swatch.className = 'metric-key-swatch';
	swatch.id = 'metric-key-swatch-' + metricName;
	swatch.style.backgroundColor = metricColor;

	var label = document.createElement('div');
	label.className = 'metric-key-label';
	label.id = 'metric-key-label-'+metricName;
	label.innerHTML = metricTitle + ': ';

	var valueLabel = document.createElement('span');
	valueLabel.className = 'metric-key-value-label';
	valueLabel.id = 'metric-key-value-label-' + metricName;
	valueLabel.innerHTML = ' ';

	metricKey.appendChild(swatch);
	metricKey.appendChild(label);
	metricKey.appendChild(valueLabel);
	legend.appendChild(metricKey);
}

// construct the widget objects using the config
function constructWidgets() {
	var graphWidgets = document.querySelectorAll('.graph-widget'); 
	var i = 0;
    for (i = 0; i < graphWidgets.length; i++) {
		var widgetElement = graphWidgets[i];
		var graphElement = widgetElement.querySelector('.graph');
		var legend = widgetElement.querySelector('.legend');
		var hoverLegend = widgetElement.querySelector('.hover-legend');
		var widgetName = $.trim(widgetElement.id);
		var widgetConfig = config.widgets[widgetName];
		var graphObject = null;
		var graphData = {};
		var graphColors = {};

		// build the structures needed for each metric
		var j = 0;
		var metricSeries = [];

		var metricName = 0;
		for (metricName in widgetConfig.metrics) {
			if (widgetConfig.metrics.hasOwnProperty(metricName)) {
				var metric = widgetConfig.metrics[metricName];

				graphData[metricName] = [{ x:0, y:0 }];
				var metricColor = metric.color || DEFAULT_GRAPH_COLOUR;
				graphColors[metricName] = metricColor;
				metricSeries[j] = {
					data: graphData[metricName],
					color: graphColors[metricName],
					name: metricName
				};

				constructMetricKey(legend, metricName, metric.title, metricColor);
				constructMetricKey(hoverLegend, metricName, metric.title, metricColor);

				j++;
			}
		}

		graphObject = new Rickshaw.Graph({
			element: graphElement,
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

		graphObject.render();

		graphs[i] = {
			name: widgetName,
			data: graphData,
			object: graphObject,
			containerElement: widgetElement
		};

		var hover = new Hover(graphs[i], widgetConfig.metrics, legend, hoverLegend);
	}
}

// construct the url to be sent as a request to the server
function constructUrl(widgetName) {
	return '/render/' + config.dashboardName + '/' + widgetName;
}

// formats an time value on the x axis into a UTC string
function XFormatter(x) { 
	return new Date(x * 1000).toUTCString(); 
}

var YFormatter = Rickshaw.Fixtures.Number.formatKMBT;
function updateLegendValues(graph) {
	var graphWidget = graph.containerElement; 
	var legend = graphWidget.querySelector('.legend');
	var timeLabel = legend.querySelector('.graph-time-label');

	var lastX = -1;
	var metrics = config.widgets[graph.name].metrics;
	var metricName = null;
	for (metricName in metrics) {
		if (metrics.hasOwnProperty(metricName)) {
			var valueLabel = legend.querySelector('#metric-key-value-label-' + metricName);
			var metricData = graph.data[metricName];
			var lastCoord = metricData[metricData.length-1];
			var lastValue = YFormatter(lastCoord.y);
			if (lastCoord.x > lastX) {
				lastX = lastCoord.x;
			}
			valueLabel.innerHTML = lastValue;
			valueLabel.className = 'metric-key-value-label inactive';
		}
	}

	timeLabel.innerHTML = XFormatter(lastX);
}

// called each update interval
function updateWidgets() {
	$.each(graphs, function(i, graph) { 
		var url = constructUrl(graph.name);
		getData(url, 
		function(results) {
			var metricName = null;
			for (metricName in results) {
				if (results.hasOwnProperty(metricName)) {
					var resultMetricData = results[metricName];
					var graphMetricData = graph.data[metricName];

					var j = 0;
					for (j = 0; j < resultMetricData.length; j++) {
						graphMetricData[j] = resultMetricData[j];
					}
				}
			}

			graph.object.update();

			updateLegendValues(graph);
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
