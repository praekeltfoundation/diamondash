diamondash.test.fixtures.add('diamondash.dashboard.DashboardModel:complex', {
  name: 'dashboard-1',
  poll_interval: 50,
  widgets: [{
    title: 'Widget 1',
    name: 'widget-1',
    type_name: 'static_toy'
  }, {
    title: 'Widget 2',
    name: 'widget-2',
    type_name: 'dynamic_toy',
    stuff: 'foo'
  }, {
    title: 'Widget 3',
    name: 'widget-3',
    type_name: 'static_toy'
  }, {
    title: 'Widget 4',
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
