var graphs = []; // rickshaw objects
var datum = []; // metric data
var aliases = []; // alias strings

// minutes of data in the live feed
var period = (typeof period == 'undefined') ? 5 : period;

function constructWidgets() {
	graphElements = document.querySelectorAll('.graph'); 

    for (var i = 0; i < graphElements.length; i++) {
        aliases[i] = 'not important';
		datum[i] = [{ x:0, y:0 }];
		graphs[i] = new Rickshaw.Graph({
			element: graphElements[i],
			interpolation: 'step-after',
			series: [{
			color: '#afdab1',
			data: datum[i]
			}]
		});
		graphs[i].render();
	}
}

var currentUrl = ""
function constructUrl(period) {
	widgetElements = document.querySelectorAll('.widget'); 

	var targets = "";
	for (var i=0; i < widgetElements.length; i++) {
		if (i != 0) {
			targets += '&';
		}
		targets += ('target=' + encodeURI($.trim(widgetElements[i].id)));
	}
	currentUrl = '/render/?' + targets + '&from=-' + period + 'minutes&format=json';

	console.log(currentUrl);
}

// refresh the graph
function refreshData(immediately) {

	getData(function(values) {
		for (var i=0; i<graphs.length; i++) {
			for (var j=0; j<values[i].length; j++) {
				if (typeof values[i][j] !== "undefined") {
					datum[i][j] = values[i][j];
				}
			}

			// we want to render immediately, i.e.
			// as soon as ajax completes
			// used for time period / pause view
			if (immediately) {
				updateGraphs(i);
			}
		}

		values = null;
	});

	// we can wait until all data is gathered, i.e.
	// the live refresh should happen synchronously
	if (!immediately) {
		for (var i=0; i<graphs.length; i++) {
			updateGraphs(i);
		}
	}
}

// retrieve the data from Graphite
function getData(dataCallback) {
	var obtainedDatum = [];
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
	}).done(function(d) {
		if (d.length > 0) {
			for (var i=0; i<d.length; i++) {
				obtainedDatum[i] = [];
				obtainedDatum[i][0] = {
					x: d[i].datapoints[0][1],
	y: d[i].datapoints[0][0] || graphs[i].lastKnownValue || 0
				};
				for (var j=1; j<d[i].datapoints.length; j++) {
					obtainedDatum[i][j] = {
						x: d[i].datapoints[j][1],
	y: d[i].datapoints[j][0] || graphs[i].lastKnownValue
					};
					if (typeof d[i].datapoints[j][0] === "number") {
						graphs[i].lastKnownValue = d[i].datapoints[j][0];
					}
				}
			} 
		}
		dataCallback(obtainedDatum);
	});
}

// perform the actual graph object and
// overlay name and number updates
function updateGraphs(i) {
	// update our graph
	graphs[i].update();
	if (datum[i][datum[i].length - 1] !== undefined) {
		var lastValue = datum[i][datum[i].length - 1].y;
		var lastValueDisplay;
		if ((typeof lastValue == 'number') && lastValue < 2.0) {
			lastValueDisplay = Math.round(lastValue*1000)/1000;
		} else {
			lastValueDisplay = parseInt(lastValue);
		}
	}
}

// build our graph objects
constructWidgets();

// build our url
constructUrl(period);

refreshData("now");

// define our refresh and start interval
var refreshInterval = (typeof refresh == 'undefined') ? 2000 : refresh;
var refreshId = setInterval(refreshData, refreshInterval);
