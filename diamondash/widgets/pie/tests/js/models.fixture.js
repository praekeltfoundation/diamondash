diamondash.test.fixtures.add('diamondash.widgets.pie.models.PieModel:simple', {
  name: 'pie-a',
  bucket_size: (5 * 1000 * 60),
  default_value: 0,
  metrics: [{
    id: 'metric-a',
    name: 'metric-a',
    datapoints: [
      {x: 1340875995000, y: 18}]
  }, {
    id: 'metric-b',
    name: 'metric-b',
    datapoints: [
      {x: 1340875995000, y: 8}]
  }, {
    id: 'metric-c',
    name: 'metric-c',
    datapoints: [
      {x: 1340875995000, y: 34}]
  }]
});
