diamondash.test.fixtures.add('diamondash.dashboard.DashboardModel:simple', {
  name: 'dashboard-1',
  poll_interval: 50,
  widgets: [{
    name: 'widget-1',
    title: 'Widget 1',
    type_name: 'toy',
    width: 3,
    stuff: 'foo'
  }, {
    name: 'widget-2',
    title: 'Widget 2',
    type_name: 'toy',
    width: 4,
    stuff: 'bar'
  }, {
    name: 'widget-3',
    title: 'Widget 3',
    type_name: 'toy',
    width: 2,
    stuff: 'baz'
  }, {
    name: 'widget-4',
    title: 'Widget 4',
    type_name: 'toy',
    width: 5,
    stuff: 'qux'
  }],
  rows: [{
    widgets: [
      {name: 'widget-1'},
      {name: 'widget-2'}]
  }, {
    widgets: [
      {name: 'widget-3'},
      {name: 'widget-4'}]
  }]
});
