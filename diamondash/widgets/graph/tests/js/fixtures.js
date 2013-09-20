diamondash.test.fixtures.add('diamondash.widgets.graph.models.GraphModel:simple', {
  step: 5,
  domain: [10, 30],
  range: [2, 24],
  metrics: [{
    name: 'foo',
    datapoints: [
      {x: 10, y: 18},
      {x: 15, y: 12},
      {x: 20, y: 6},
      {x: 25, y: 16},
      {x: 30, y: 24}]
  }, {
    name: 'bar',
    datapoints: [
      {x: 10, y: 8},
      {x: 15, y: 22},
      {x: 20, y: 2},
      {x: 25, y: 8},
      {x: 30, y: 16}]
  }]
});
