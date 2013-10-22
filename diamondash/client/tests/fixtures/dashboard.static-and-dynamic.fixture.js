diamondash.test.fixtures.add('diamondash.dashboard.DashboardModel:static-and-dynamic', {
  name: 'dashboard-1',
  poll_interval: 50,
  widgets: [{
    name: 'widget-1',
    type_name: 'static_toy'
  }, {
    name: 'widget-2',
    type_name: 'dynamic_toy',
    stuff: 'foo'
  }, {
    name: 'widget-3',
    type_name: 'static_toy'
  }, {
    name: 'widget-4',
    type_name: 'dynamic_toy',
    stuff: 'bar'
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
