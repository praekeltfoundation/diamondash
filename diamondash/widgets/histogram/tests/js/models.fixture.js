diamondash.test.fixtures.add('diamondash.widgets.histogram.models.HistogramModel:simple', {
  name: 'histogram-a',
  bucket_size: (5 * 1000 * 60),
  default_value: 0,
  metrics: [{
    id: 'metric-a',
    name: 'metric-a',
    datapoints: [
      {x: 1340875995000, y: 18},
      {x: 1340876295000, y: 12},
      {x: 1340876595000, y: 6},
      {x: 1340876895000, y: 3},
      {x: 1340877195000, y: 9},
      {x: 1340877495000, y: 24}]
  }]
});
