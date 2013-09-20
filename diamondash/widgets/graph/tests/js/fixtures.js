diamondash.test.fixtures.add('diamondash.widgets.graph.models.GraphModel:simple', {
  step: (5 * 1000 * 60),
  domain: [1340875995000, 1340877495000],
  range: [2, 24],
  metrics: [{
    name: 'foo',
    datapoints: [
      {x: 1340875995000, y: 18},
      {x: 1340876295000, y: 12},
      {x: 1340876595000, y: 6},
      {x: 1340876895000, y: 16},
      {x: 1340877195000, y: 14},
      {x: 1340877495000, y: 24}]
  }, {
    name: 'bar',
    datapoints: [
      {x: 1340875995000, y: 8},
      {x: 1340876295000, y: 22},
      {x: 1340876595000, y: 2},
      {x: 1340876895000, y: 8},
      {x: 1340877195000, y: 12},
      {x: 1340877495000, y: 16}]
  }]
});
