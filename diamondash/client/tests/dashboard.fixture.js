diamondash.test.fixtures.add('diamondash.dashboard.DashboardModel:simple', {
  name: 'dashboard-1',
  poll_interval: 50,
  widgets: [{
    name: 'widget-1',
    type: 'static_toy'
  }, {
    name: 'widget-2',
    type: 'dynamic_toy',
    stuff: 'foo'
  }, {
    name: 'widget-3',
    type: 'static_toy'
  }, {
    name: 'widget-4',
    type: 'dynamic_toy',
    stuff: 'bar'
  }]
});
