var graphs = []; // rickshaw objects
var data = []; // metric data

// minutes of data in the live feed
var period = (typeof period == 'undefined') ? 5 : period;

function constructWidgets() {
	graphElements = document.querySelectorAll('.graph'); 

    for (var i = 0; i < graphElements.length; i++) {
		data[i] = [{ x:0, y:0 }];
		graphs[i] = new Rickshaw.Graph({
			element: graphElements[i],
			interpolation: 'step-after',
			series: [{
			color: '#afdab1',
			data: data[i]
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
}

// refresh the graph
function updateWidgets() {
	getData(function(values) {
		for (var i = 0; i < graphs.length; i++) {
			for (var j = 0; j < values[i].length; j++) {
				if (typeof values[i][j] !== "undefined") {
					data[i][j] = values[i][j];
				}
			}
			updateGraph(i);
		}

		values = null;
	});
}

// retrieve the data from Graphite
function getData(cbDataReceived) {
	var obtainedData = [];
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
			for (var i = 0; i < d.length; i++) {
				obtainedData[i] = [];
				obtainedData[i][0] = {
					x: d[i].datapoints[0][1],
					y: d[i].datapoints[0][0] || graphs[i].lastKnownValue || 0
				};
				for (var j = 1; j < d[i].datapoints.length; j++) {
					obtainedData[i][j] = {
						x: d[i].datapoints[j][1],
						y: d[i].datapoints[j][0] || graphs[i].lastKnownValue
					};
					if (typeof d[i].datapoints[j][0] === "number") {
						graphs[i].lastKnownValue = d[i].datapoints[j][0];
					}
				}
			} 
		}
		cbDataReceived(obtainedData);
	});
}

// perform the actual graph object and
// overlay name and number updates
function updateGraph(i) {
	// update our graph
	graphs[i].update();
	if (data[i][data[i].length - 1] !== undefined) {
		var lastValue = data[i][data[i].length - 1].y;
		var lastValueDisplay;
		if ((typeof lastValue == 'number') && lastValue < 2.0) {
			lastValueDisplay = Math.round(lastValue*1000)/1000;
		} else {
			lastValueDisplay = parseInt(lastValue);
		}
	}
}

constructWidgets();
constructUrl(period);

updateWidgets(true);

// define our refresh and start interval
var updateInterval = (typeof refresh == 'undefined') ? 2000 : refresh;
var updateId = setInterval(updateWidgets, updateInterval);
