diamondash.test.fixtures.add('diamondash.widgets.graph.models.GraphModel:simple', {
  name: 'graph-a',
  bucket_size: (5 * 1000 * 60),
  default_value: 0,
  metrics: [{
    id: 'metric-a',
    name: 'metric-a',
    datapoints: [
      {x: 1340875995000, y: 18},
      {x: 1340876295000, y: 12},
      {x: 1340876595000, y: 6},
      {x: 1340876895000, y: 16},
      {x: 1340877195000, y: 14},
      {x: 1340877495000, y: 24}]
  }, {
    id: 'metric-b',
    name: 'metric-b',
    datapoints: [
      {x: 1340875995000, y: 8},
      {x: 1340876295000, y: 22},
      {x: 1340876595000, y: 2},
      {x: 1340876895000, y: 8},
      {x: 1340877195000, y: 12},
      {x: 1340877495000, y: 16}]
  }]
});
