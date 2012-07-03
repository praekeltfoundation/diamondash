var graphs = []; // rickshaw objects
var requestInterval = (config.requestInterval is undefined) ? 2000 : (config.requestInterval * 1000);

function constructWidgets() {
	graphElements = document.querySelectorAll('.graph'); 
    for (var i = 0; i < graphElements.length; i++) {
		widgetName = $.trim(graphElements[i].id)
		graphs[i] = {
			'name': widgetName,
			'data': [{ x:0, y:0 }],
			'object': undefined
		};
		
		graphs[i].object = new Rickshaw.Graph({
			element: graphElements[i],
			renderer: 'line',
			series: [{
				color: '#0051cc',
				data: graphs[i].data 
			}]
		});

		graphs[i].object.render();
	}
}

function constructUrl(widgetName) {
	return '/render/' + dashboardName + '/' + widgetName;
}

function updateWidgets() {
	$.each(graphs, function(i, graph) { 
		url = constructUrl(graph.name)
		getData(url, 
		function(values) {
			for (var j = 0; j < values.length; j++)
				graph.data[j] = values[j];
			graph.object.update();
			values = null;
		});
	});
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

var updateId = setInterval(updateWidgets, requestInterval);
