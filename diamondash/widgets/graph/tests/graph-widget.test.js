var GraphWidgetModel = diamondash.widgets.GraphWidgetModel,
    GraphWidgetView = diamondash.widgets.GraphWidgetView;

describe("GraphWidgetModel", function(){
  describe(".initialize()", function() {
    it("should bind the model's metrics' events to the model correctly",
       function() {
      var model = new GraphWidgetModel({
        metrics: [
          {name: 'm1', title: 'metric 1'},
          {name: 'm2', title: 'metric 2'}]
      });

      assert(typeof model.get('metrics') !== "undefined");

      var modelChanged = false,
          metricsChanged = false,
          metricsAdded = false,
          metricsRemoved = false,
          metricsReset = false;

      var metrics = model.get('metrics');


      model.on('change', function() { modelChanged = true; });
      model.on('change:metrics', function() { metricsChanged = true; });
      metrics.update({name: 'm1', title: 'aaah'});
      assert(modelChanged);
      assert(metricsChanged);

      model.on('add:metrics', function() { metricsAdded = true; });
      metrics.add({name: 'm3', title: 'larp'});
      assert(metricsAdded);

      model.on('remove:metrics', function() { metricsRemoved = true; });
      metrics.remove(metrics.get('m1'));
      assert(metricsRemoved);

      model.on('reset:metrics', function() { metricsReset = true; });
      metrics.reset();
      assert(metricsReset);
    });
  });

  describe(".parse()", function() {
    it("should update the model's metrics with new datapoints", function() {
      var model = new GraphWidgetModel({
        'metrics': [
          {name: 'm1', datapoints: [{x: 0, y: 1}, {x: 1, y: 3}]},
          {name: 'm2', datapoints: [{x: 0, y: 8}, {x: 1, y: 9}]}]
      });

      model.parse({
        'domain': [3, 5],
        'range': [3, 11],
        'metrics': [
           {name: 'm1', datapoints: [{x: 3, y: 9}, {x: 5, y: 3}]},
           {name: 'm2', datapoints: [{x: 3, y: 8}, {x: 5, y: 11}]}]
      });

      assert.deepEqual(model.get('domain'), [3, 5]);
      assert.deepEqual(model.get('range'), [3, 11]);

      assert.deepEqual(
        model.get('metrics')
             .get('m1')
             .get('datapoints'),
        [{x: 3, y: 9}, {x: 5, y: 3}]);

      assert.deepEqual(
        model.get('metrics')
             .get('m2')
             .get('datapoints'),
        [{x: 3, y: 8}, {x: 5, y: 11}]);
    });
  });
});
