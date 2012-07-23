/*
 * Class for the diamondash graph widget
 */

var DEFAULT_GRAPH_COLOR = '#3333cc';
var DEFAULT_GRAPH_WARNING_COLOR = '#cc3333';

Metric = function(args) {
	this.name = args.name;
	this.mConfig = args.mConfig;
	this.minThreshold = this.mConfig.warning_min_threshold;
	this.maxThreshold = this.mConfig.warning_max_threshold;
	this.graphWidget = args.graphWidget;
	this.graphAttrs = {};
	this.mLegend = {};
	this.mHoverLegend = {};
	this.prevWarning = null;

	this.init(args);
};

Metric.prototype = {
	init: function(args) {
		var legend = this.graphWidget.legend;
		var hoverLegend = this.graphWidget.hoverLegend;

		if (typeof this.mConfig.color === 'undefined') {
			this.mConfig.color = DEFAULT_GRAPH_COLOR;
		}

		if ((typeof this.minThreshold !== 'undefined' 
				|| typeof this.maxThreshold !== 'undefined')
			&& typeof this.mConfig.warning_color === 'undefined') {
				this.mConfig.warning_color = DEFAULT_GRAPH_WARNING_COLOR;
			}

		this.graphAttrs = {
			data: [{ x:0, y:0 }],
			color: this.mConfig.color,
			name: this.name
		};

		this.mLegend = this.buildMetricKey(legend);
		this.mHoverLegend = this.buildMetricKey(hoverLegend);
	},

	getGraphAttrs: function() {
		return this.graphAttrs;
	},

	getData: function() {
		return this.graphAttrs.data;
	},

	enableWarning: function() {
		this.setColor(this.mConfig.warning_color);
		this.mLegend.valueLabel.style.color = this.mConfig.warning_color;
		this.mHoverLegend.valueLabel.style.color = this.mConfig.warning_color;
	},

	disableWarning: function() {
		this.setColor(this.mConfig.color);
		this.mLegend.valueLabel.style.color = '#000';
		this.mHoverLegend.valueLabel.style.color = '#000';
	},

	warningThresholdReached: function(coord) {
		if (this.prevWarning !== null
			&& coord.x === this.prevWarning.x 
			&& coord.y === this.prevWarning.y) {
			return false;
		}

		reached = ((typeof this.minThreshold !== 'undefined' 
					&& coord.y < this.minThreshold) 
				|| (typeof this.maxThreshold !== 'undefined' 
					&& coord.y > this.maxThreshold));

		if (reached) {
			this.prevWarning = coord;
		}

		return reached;
	},

	setData: function(data) {
		this.graphAttrs.data = data;

		var lastCoord = data[data.length-1];
		var lastValue = yFormatter(lastCoord.y);
		this.mLegend.valueLabel.innerHTML = lastValue;
		this.mLegend.valueLabel.className = 'metric-key-value-label inactive';

		if (this.warningThresholdReached(lastCoord)) {
			this.graphWidget.warningSwitch.flagMetric(this);
		}
	},

	pushData: function(data) {
		this.graphAttrs.push(data);
	},

	getColor: function() {
		return this.graphAttrs.color;
	},

	setColor: function(color) {
		this.graphAttrs.color = color;
		this.mLegend.swatch.style.backgroundColor = color;
		this.mHoverLegend.swatch.style.backgroundColor = color;
	},

	// Build metric's key in the legend
	buildMetricKey: function(legend) {
		var metricKey = document.createElement('div');
		metricKey.id = 'metric-key-container-' + this.name;
		metricKey.className = 'metric-key-container';

		var swatch = document.createElement('div');
		swatch.className = 'metric-key-swatch';
		swatch.id = 'metric-key-swatch-' + this.name;
		swatch.style.backgroundColor = this.mConfig.color;

		var label = document.createElement('div');
		label.className = 'metric-key-label';
		label.id = 'metric-key-label-' + this.name;
		label.innerHTML = this.mConfig.title + ': ';

		var valueLabel = document.createElement('span');
		valueLabel.className = 'metric-key-value-label';

		valueLabel.id = 'metric-key-value-label-' + this.name;
		valueLabel.innerHTML = ' ';

		metricKey.appendChild(swatch);
		metricKey.appendChild(label);
		metricKey.appendChild(valueLabel);
		legend.appendChild(metricKey);

		return { 
			valueLabel: valueLabel,
				swatch: swatch
		};
	}
};


function WarningSwitch(args) {
	this.graphWidget = args.graphWidget;
	this.flaggedMetrics = [];
}

WarningSwitch.prototype = {
	flagMetric: function(metric) {
		this.flaggedMetrics.push(metric);
		metric.enableWarning();
	},

	disable: function() {
		var i = null;
		for (i in this.flaggedMetrics) {
			if (this.flaggedMetrics.hasOwnProperty(i)) {
				var metric = this.flaggedMetrics[i];
				metric.disableWarning();
			}
		}

		this.graphWidget.object.update();
	}
};

function GraphWidget(args) {
	Widget.call(this, args);
	this.metrics = [];
	this.warningSwitch = new WarningSwitch({
		graphWidget: this
	});

	this.init(args);
}
GraphWidget.subclass(Widget);

GraphWidget.prototype = {
	init: function(args) {
		var graphElement = this.element.querySelector('.graph');
		this.legend = this.element.querySelector('.legend');
		this.timeLabel = this.legend.querySelector('.graph-time-label');
		this.hoverLegend = this.element.querySelector('.hover-legend');
		this.hoverTimeLabel = this.hoverLegend.querySelector('.graph-time-label');


		// disable the warning color switch when a graph is clicked on
		graphElement.onclick = $.proxy(this.warningSwitch.disable, this.warningSwitch);

		// build metrics
		var metricName = null;
		var series = [];
		for (metricName in this.config.metrics) {
			if (this.config.metrics.hasOwnProperty(metricName)) {
				var mConfig = this.config.metrics[metricName];

				metric = new Metric({
					name: metricName,
					mConfig: mConfig,
					graphWidget: this
				});

				this.metrics[metricName] = metric;
				series.push(metric.getGraphAttrs());
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

		var hover = new Hover({
			graphObject: this.object, 
			mConfigs: this.config.metrics, 
			legend: this.legend,
			hoverLegend: this.hoverLegend, 
			hoverTimeLabel: this.hoverTimeLabel
		});

		this.object.render();
	},

	update: function(results) {
		var lastX = -1;
		var metricName = null;
		for (metricName in results) {
			if (results.hasOwnProperty(metricName)) {
				data = results[metricName];
				this.metrics[metricName].setData(data);

				lastCoords = data[data.length-1];
				if (lastCoords.x > lastX) {
					lastX = lastCoords.x;
				}
			}
		}

		this.timeLabel.innerHTML = xFormatter(lastX);

		this.object.update();
	},


	Metric: Metric,
};

// formats an time value on the x axis into a UTC string
function xFormatter(x) { 
	return new Date(x * 1000).toUTCString(); 
}

var yFormatter = Rickshaw.Fixtures.Number.formatKMBT;

function Hover(args) {
	legend = args.legend; 
	graphObject = args.graphObject; 
	mConfigs = args.mConfigs; 
	hoverLegend = args.hoverLegend; 
	hoverTimeLabel = args.hoverTimeLabel;

	var HoverDetail = (function(legend, graphObject, mConfigs, 
				                hoverLegend, hoverTimeLabel) {
		return Rickshaw.Class.create(Rickshaw.Graph.HoverDetail, {
			render: function(args) {
				hoverTimeLabel.innerHTML = args.formattedXValue;

				// for each metric
				args.detail.sort(
					function(a, b) { 
						return a.order - b.order;
					}).forEach(
						function(d) {
							var title = mConfigs[d.name].title;
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
	}(legend, graphObject, mConfigs, 
	  hoverLegend, hoverTimeLabel));

	return new HoverDetail({graph: graphObject});
}
