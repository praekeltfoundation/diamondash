describe("diamondash.dashboard", function(){
  var utils = diamondash.test.utils,
      widgets = diamondash.widgets,
      widget = diamondash.widgets.widget,
      dynamic = diamondash.widgets.dynamic,
      dashboard = diamondash.dashboard,
      fixtures = diamondash.test.fixtures;

  var ToyWidgetView = widget.WidgetView.extend({
    render: function() {
      this.$el.text(this.model.get('stuff'));
    }
  });

  beforeEach(function() {
    widgets.registry.views.add('toy', ToyWidgetView);
  });

  afterEach(function() {
    utils.unregisterModels();
    widgets.registry.views.remove('toy');
  });

  describe(".DashboardModel", function() {
    var server,
        clock,
        model,
        widget2,
        widget4;

    var StaticToyWidgetModel = widget.WidgetModel.extend();
    var DynamicToyWidgetModel = dynamic.DynamicWidgetModel.extend();

    beforeEach(function() {
      clock = sinon.useFakeTimers();
      server = sinon.fakeServer.create();

      widgets.registry.models.add('static_toy', StaticToyWidgetModel);
      widgets.registry.models.add('dynamic_toy', DynamicToyWidgetModel);

      model = new dashboard.DashboardModel(fixtures.get(
        'diamondash.dashboard.DashboardModel:complex'));

      widget2 = model.get('widgets').get('widget-2');
      widget4 = model.get('widgets').get('widget-4');
    });

    afterEach(function() {
      clock.restore();
      server.restore();

      model.stopPolling();

      widgets.registry.models.remove('dynamic_toy');
      widgets.registry.models.remove('static_toy');
    });

    describe(".fetchSnapshots()", function() {
      it("should fetch the snaphots of its dynamic widgets", function() {
        server.respondWith(
          '/api/widgets/dashboard-1/widget-2/snapshot',
          JSON.stringify({stuff: 'spam'}));

        server.respondWith(
          '/api/widgets/dashboard-1/widget-4/snapshot',
          JSON.stringify({stuff: 'ham'}));

        assert.equal(widget2.get('stuff'), 'foo');
        assert.equal(widget4.get('stuff'), 'bar');

        model.fetchSnapshots();
        server.respond();

        assert.equal(widget2.get('stuff'), 'spam');
        assert.equal(widget4.get('stuff'), 'ham');
      });
    });

    describe(".poll()", function() {
      beforeEach(function() {
        server.autoRespond = true;
        server.autoRespondAfter = 1;
      });

      it("should issue snapshot requests immediately", function() {
        server.respondWith(
          '/api/widgets/dashboard-1/widget-2/snapshot',
          JSON.stringify({stuff: 'spam'}));

        server.respondWith(
          '/api/widgets/dashboard-1/widget-4/snapshot',
          JSON.stringify({stuff: 'ham'}));

        assert.equal(widget2.get('stuff'), 'foo');
        assert.equal(widget4.get('stuff'), 'bar');

        model.poll();
        server.respond();

        assert.equal(widget2.get('stuff'), 'spam');
        assert.equal(widget4.get('stuff'), 'ham');
      });

      it("should issue snapshot requests each poll interval", function() {
        var responses = {
          widget2: [
            {stuff: 'spam-0'},
            {stuff: 'spam-1'},
            {stuff: 'spam-2'}],
          widget4: [
            {stuff: 'ham-0'},
            {stuff: 'ham-1'},
            {stuff: 'ham-2'}]
        };

        server.respondWith(
          '/api/widgets/dashboard-1/widget-2/snapshot',
          function(req) {
            var res = responses.widget2.shift();
            req.respond(200, [], JSON.stringify(res));
          });

        server.respondWith(
          '/api/widgets/dashboard-1/widget-4/snapshot',
          function(req) {
            var res = responses.widget4.shift();
            req.respond(200, [], JSON.stringify(res));
          });

        model.poll();
        assert.equal(widget2.get('stuff'), 'foo');
        assert.equal(widget4.get('stuff'), 'bar');

        clock.tick(1);
        assert.equal(widget2.get('stuff'), 'spam-0');
        assert.equal(widget4.get('stuff'), 'ham-0');

        clock.tick(50);
        assert.equal(widget2.get('stuff'), 'spam-1');
        assert.equal(widget4.get('stuff'), 'ham-1');

        clock.tick(50);
        assert.equal(widget2.get('stuff'), 'spam-2');
        assert.equal(widget4.get('stuff'), 'ham-2');
      });
    });

    describe(".stopPolling()", function() {
      beforeEach(function() {
        server.autoRespond = true;
        server.autoRespondAfter = 1;
      });

      it("should stop disable polling", function() {
        var polls = 0;

        server.respondWith(
          '/api/widgets/dashboard-1/widget-2/snapshot',
          function(req) {
            polls++;
            req.respond(200, [], '{}');
          });

        model.poll();
        assert.equal(polls, 0);

        clock.tick(1);
        assert.equal(polls, 1);

        clock.tick(50);
        assert.equal(polls, 2);

        model.stopPolling();

        clock.tick(50);
        assert.equal(polls, 2);
      });
    });
  });

  describe(".DashboardView", function() {
    var view;

    beforeEach(function() {
      view = new dashboard.DashboardView({
        model: new dashboard.DashboardModel(fixtures.get(
          'diamondash.dashboard.DashboardModel:simple'))
      });
    });

    describe(".render()", function() {
      it("should render its widgets", function() {
        assert.equal(view.$('#widget-1').text(), '');
        assert.equal(view.$('#widget-2').text(), '');

        view.render();

        assert.equal(view.$('#widget-1').text(), 'foo');
        assert.equal(view.$('#widget-2').text(), 'bar');
      });
    });
  });

  describe("DashboardWidgetViews", function() {
    var views;

    beforeEach(function() {
      var dashboardView = new dashboard.DashboardView({
        model: new dashboard.DashboardModel(fixtures.get(
          'diamondash.dashboard.DashboardModel:simple'))
      });

      views = dashboardView.widgets;
    });

    describe(".add", function() {
      it("should allowing adding widget instances", function() {
        var widgetN = new ToyWidgetView({
          model: new widget.WidgetModel({
            name: 'widget-n',
            type_name: 'toy'
          })
        });

        views.add(widgetN);

        assert.strictEqual(views.get('widget-n'), widgetN);
      });

      it("should allow adding widgets from an options object", function() {
        views.add({
          model: new widget.WidgetModel({
            name: 'widget-n',
            type_name: 'toy'
          })
        });

        assert(views.get('widget-n') instanceof ToyWidgetView);
      });
    });
  });
});
