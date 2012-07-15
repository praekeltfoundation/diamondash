var DEFAULT_GRAPH_COLOUR = '#3333cc';
var DEFAULT_GRAPH_WARNING_COLOR = '#cc3333';

/*
 * Class for the diamondash graph widget
 */

function GraphWidget(args) {
	this.seriesLookup = {};
	this.name = args.name;
	this.config = args.config;
	this.element = args.element;

	this.initialize();
}

GraphWidget.prototype.getMetricData = function(metricName) {
	return this.seriesLookup[metricName].data;
};

GraphWidget.prototype.setMetricData = function(metricName, data) {
	this.seriesLookup[metricName].data = data;
};

GraphWidget.prototype.pushMetricData = function(metricName, data) {
	this.seriesLookup[metricName].push(data);
};

GraphWidget.prototype.getMetricColor = function(metricName) {
	return this.seriesLookup[metricName].color;
};

GraphWidget.prototype.setMetricColor = function(metricName, color) {
	this.seriesLookup[metricName].color = color;
};

GraphWidget.prototype.initialize = function() {
	var graphElement = this.element.querySelector('.graph');
	this.legend = this.element.querySelector('.legend');
	this.hoverLegend = this.element.querySelector('.hover-legend');
	this.timeLabel = this.legend.querySelector('.graph-time-label');
	this.hoverTimeLabel = this.hoverLegend.querySelector('.graph-time-label');

	series = [];

	// build metrics
	var metricName = null;
	for (metricName in this.config.metrics) {
		if (this.config.metrics.hasOwnProperty(metricName)) {
			var metricConfig = this.config.metrics[metricName];

			if (typeof metricConfig.color === 'undefined') {
				metricConfig.color = DEFAULT_GRAPH_COLOUR;
			}
			var metricColor = metricConfig.color;

			if (typeof metricConfig.warning_min_threshold !== 'undefined'
			&& typeof metricConfig.warning_max_threshold !== 'undefined'
			&& typeof metricConfig.warning_color === 'undefined') {
				metricConfig.warning_color = DEFAULT_GRAPH_WARNING_COLOR;
			}

			metric = {
				data: [{ x:0, y:0 }],
				color: metricConfig.color,
				name: metricName
			};

			this.seriesLookup[metricName] = metric;
			series.push(metric);
			buildMetricKey(this.legend, metricName, metricConfig.title, metricColor);
			buildMetricKey(this.hoverLegend, metricName, metricConfig.title, metricColor);
		}
	}

	this.object = new Rickshaw.Graph({
		element: graphElement,
		renderer: 'line',
		series: series
	});

	var xAxis = new Rickshaw.Graph.Axis.Time({
		graph: this.object 
	});

	var yAxis = new Rickshaw.Graph.Axis.Y({
		element: this.element.querySelector('.y-axis'),
		orientation: 'left',
		graph: this.object,
		tickFormat: Rickshaw.Fixtures.Number.formatKMBT,
	});

	var hover = new Hover(this.object, this.config.metrics, this.legend,
			              this.hoverLegend, this.hoverTimeLabel);

	this.object.render();
};

GraphWidget.prototype.update = function(results) {
	var metricName = null;
	for (metricName in results) {
		if (results.hasOwnProperty(metricName)) {
			this.setMetricData(metricName, results[metricName]);
		}
	}

	this.updateGraphDetails();
	this.object.update();
};

function warningThresholdReached(minThreshold, maxThreshold, value) {
	return ((typeof minThreshold !== 'undefined'
			&& value < minThreshold)
		|| (typeof maxThreshold !== 'undefined'
			&& value > maxThreshold));
}

// formats an time value on the x axis into a UTC string
function xFormatter(x) { 
	return new Date(x * 1000).toUTCString(); 
}

var yFormatter = Rickshaw.Fixtures.Number.formatKMBT;
GraphWidget.prototype.updateGraphDetails = function() {
	// for each metric, update legend values and color, as well as graph color
	var lastX = -1;
	var metrics = this.config.metrics;
	var metricName = null;
	for (metricName in metrics) {
		if (metrics.hasOwnProperty(metricName)) {
			var metric = metrics[metricName];
			var valueLabel = this.legend.querySelector(
				'#metric-key-value-label-' + metricName);
			var swatch = this.legend.querySelector(
				'#metric-key-swatch-' + metricName);
			var hoverSwatch = this.hoverLegend.querySelector(
				'#metric-key-swatch-' + metricName);
			var metricData = this.getMetricData(metricName);
			var lastCoord = metricData[metricData.length-1];
			var lastValue = yFormatter(lastCoord.y);
			if (lastCoord.x > lastX) {
				lastX = lastCoord.x;
			}
			valueLabel.innerHTML = lastValue;
			valueLabel.className = 'metric-key-value-label inactive';

			if (warningThresholdReached(metric.warning_min_threshold, 
				metric.warning_max_threshold, lastCoord.y)) {
				var warning_color = metric.warning_color;
				this.setMetricColor(metricName, warning_color);
				valueLabel.style.color = warning_color;
				swatch.style.backgroundColor = warning_color;
				hoverSwatch.style.backgroundColor = warning_color;
			} else {
				this.setMetricColor(metricName, metric.color);
				valueLabel.style.color = '';
				swatch.style.backgroundColor = metric.color;
				hoverSwatch.style.backgroundColor = metric.color;
			}
		}
	}

	this.timeLabel.innerHTML = xFormatter(lastX);
};

// Build the passed in metric's key in the legend
function buildMetricKey(legend, metricName, metricTitle, metricColor) {
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

function Hover(graphObject, widgetMetricsConfig, legend, 
		       hoverLegend, hoverTimeLabel) {
	var HoverDetail = Rickshaw.Class.create(Rickshaw.Graph.HoverDetail, {
		render: function(args) {
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
						dot.style.top = graphObject.y(d.value.y0 + d.value.y) + 'px';
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

	return new HoverDetail({graph: graphObject});
}
