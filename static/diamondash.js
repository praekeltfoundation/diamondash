var graphs = []; // rickshaw objects
var widgetElements = document.querySelectorAll('.widget')
var dashboardName = 'test_dashboard' // TODO change to support multiple dashboards

function constructWidgets() {
	graphElements = document.querySelectorAll('.graph'); 
    for (var i = 0; i < graphElements.length; i++) {
		graphs[i] = new Rickshaw.Graph({
			element: graphElements[i],
			interpolation: 'step-after',
			series: [{
			color: '#afdab1',
			data: [{ x:0, y:0 }]
			}]
		});

		graphs[i].render();
	}
}

function constructUrl(widgetElement) {
	return '/render/' + dashboardName + '/' + $.trim(widgetElements[i].id);
}

function updateWidgets() {
	for (var i = 0; i < widgetElements.length; i++) {
		url = constructUrl(widgetElement)
		getData(url, function(values) {
				for (var j = 0; j < values.length; j++) {
						graphs[i].data[j] = values[j];
					}
				}
				graphs[i].update();
			}

			values = null;
		});
	}
}

// retrieve the data from Graphite
function getData(currentUrl, cbDataReceived) {
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
	}).done(function(responseData) {
		if (responseData.length > 0)
		    cbDataReceived(responseData);
	});
}

constructWidgets();
updateWidgets();

var updateInterval = (typeof refresh == 'undefined') ? 2000 : refresh;
var updateId = setInterval(updateWidgets, updateInterval);
