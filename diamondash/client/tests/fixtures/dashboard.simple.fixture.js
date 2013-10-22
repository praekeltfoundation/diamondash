diamondash.test.fixtures.add('diamondash.dashboard.DashboardModel:simple', {
  name: 'dashboard-1',
  poll_interval: 50,
  widgets: [{
    title: 'Widget 1',
    name: 'widget-1',
    type_name: 'toy',
    stuff: 'foo'
  }, {
    title: 'Widget 2',
    name: 'widget-2',
    type_name: 'toy',
    stuff: 'bar'
  }],
  rows: [{
    widgets: [
      {name: 'widget-1'},
      {name: 'widget-2'}]
  }]
});
