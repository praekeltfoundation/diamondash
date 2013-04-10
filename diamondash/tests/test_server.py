"""Tests for diamondash's server"""

import json

from twisted import web
from twisted.web import http
from twisted.trial import unittest
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, gatherResults
from twisted.web.template import flattenString

from diamondash import utils
from diamondash.widgets.widget import Widget
from diamondash.widgets.dynamic import DynamicWidget
from diamondash.dashboard import Dashboard, DashboardPage
from diamondash.server import DiamondashServer, DashboardIndexListItem


class StubbedDashboard(Dashboard):
    def add_widget(self, widget):
        self.widgets.append(widget)
        self.widgets_by_name[widget.name] = widget


class MockLeafResource(Resource):
    isLeaf = True

    def __init__(self, content):
        self.content = content

    def render(self, request):
        return self.content


class MockDirResource(Resource):
    isLeaf = False

    def __init__(self, children):
        self.children = children

    def getChild(self, name, request):
        return self.children.get(name)


class MockError(Exception):
    """I am fake"""


def mk_dashboard(**kwargs):
    kwargs = utils.update_dict({
        'name': 'some-dashboard',
        'title': 'Some Dashboard',
        'widgets': [],
        'client_config': {},
    }, kwargs)
    return StubbedDashboard(**kwargs)


class ToyDynamicWidget(DynamicWidget):
    TYPE_NAME = 'dynamic_toy'

    def get_snapshot(self):
        return [self.name]


class ToyStaticWidget(Widget):
    TYPE_NAME = 'static_toy'


class MockIndex(MockLeafResource):
    def __init__(self, dashboards=[]):
        MockLeafResource.__init__(self, 'mock-index')
        self.dashboards = dashboards

    def add_dashboard(self, dashboard):
        self.dashboards.append(dashboard)


class DiamondashServerTestCase(unittest.TestCase):
    def setUp(self):
        self.patch(Dashboard, 'from_config', classmethod(
           lambda cls, config, class_defaults: mk_dashboard(**config)))

        js_resources = MockDirResource({
            'a.js': MockLeafResource('mock-a.js'),
            'b.js': MockLeafResource('mock-b.js'),
        })
        css_resources = MockDirResource({
            'a.css': MockLeafResource('mock-a.css'),
            'b.css': MockLeafResource('mock-b.css'),
        })
        resources = MockDirResource({
            'js': js_resources,
            'css': css_resources,
        })

        widget1 = self.mk_dynamic_widget(
            name='widget-1',
            title='Widget 1')
        widget2 = self.mk_static_widget(
            name='widget-2',
            title='Widget 2')
        self.dashboard1 = mk_dashboard(
            name='dashboard-1',
            title='Dashboard 1',
            share_id='dashboard-1-share-id',
            widgets=[widget1, widget2])
        self.dashboard2 = mk_dashboard(name='dashboard-2', title='Dashboard 2')

        self.server = DiamondashServer(MockIndex(), resources,
                                       [self.dashboard1, self.dashboard2])
        return self.start_server()

    def tearDown(self):
        return self.stop_server()

    @inlineCallbacks
    def start_server(self):
        site_factory = Site(self.server.app.resource())
        self.ws = yield reactor.listenTCP(0, site_factory)
        addr = self.ws.getHost()
        self.url = "http://%s:%s" % (addr.host, addr.port)

    def stop_server(self):
        return self.ws.loseConnection()

    def mk_dynamic_widget(self, **kwargs):
        return ToyDynamicWidget(**utils.update_dict({
            'name': 'some-dynamic-widget',
            'title': 'Some Dynamic Widget',
            'backend': None,
            'time_range': 3600,
        }, kwargs))

    def mk_static_widget(self, **kwargs):
        return ToyStaticWidget(**utils.update_dict({
            'name': 'some-static-widget',
            'title': 'Some Static Widget',
        }, kwargs))

    def request(self, path, **kwargs):
        d = utils.http_request("%s%s" % (self.url, path), **kwargs)
        return d

    def assert_response(self, d, body, code=http.OK, headers={}):
        def got_response(response):
            self.assertEqual(response['status'], str(code))
            self.assertEqual(response['body'], body)
            for field, value in headers.iteritems():
                self.assertEqual(response['headers'][field], value)
        d.addCallback(got_response)
        return d

    def assert_json_response(self, d, data, code=http.OK, headers={}):
        headers.update({'content-type': ['application/json']})
        return self.assert_response(d, json.dumps(data), code, headers)

    def assert_unhappy_response(self, d, code):
        def trap_failure(failure):
            failure.trap(web.error.Error)
            self.assertEqual(failure.value.status, str(code))

        # fail if the failure was not trapped
        d.addCallback(lambda _: self.fail())
        d.addErrback(trap_failure)
        return d

    def assert_rendering(self, deferred_res, expected_element):
        d = flattenString(None, expected_element)
        d.addCallback(lambda body: self.assert_response(deferred_res, body))
        return d

    def test_index_rendering(self):
        return self.assert_response(self.request('/'), 'mock-index')

    def test_static_resource_rendering(self):
        def request_and_assert(path, expected):
            return self.assert_response(self.request(path), expected)

        return gatherResults([
            request_and_assert('/js/a.js', 'mock-a.js'),
            request_and_assert('/js/b.js', 'mock-b.js'),
            request_and_assert('/shared/js/a.js', 'mock-a.js'),
            request_and_assert('/shared/js/b.js', 'mock-b.js'),
            request_and_assert('/css/a.css', 'mock-a.css'),
            request_and_assert('/css/b.css', 'mock-b.css'),
            request_and_assert('/shared/css/a.css', 'mock-a.css'),
            request_and_assert('/shared/css/b.css', 'mock-b.css'),
        ])

    def test_dashboard_rendering(self):
        return self.assert_rendering(
            self.request('/dashboard-1'), DashboardPage(self.dashboard1))

    def test_dashboard_rendering_for_non_existent_dashboards(self):
        return self.assert_unhappy_response(
            self.request('/dashboard-3'), http.NOT_FOUND)

    def test_shared_dashboard_rendering(self):
        return self.assert_rendering(
            self.request('/shared/dashboard-1-share-id'),
            DashboardPage(self.dashboard1))

    def test_shared_dashboard_rendering_for_non_existent_dashboards(self):
        return self.assert_unhappy_response(
            self.request('/shared/dashboard-3-share-id'), http.NOT_FOUND)

    def test_unhandled_api_error_trapping(self):
        def unruly_method():
            raise MockError()

        @self.server.app.route('/test')
        def api_method(slf, request):
            self.server.api_call(request, unruly_method)

        return self.assert_unhappy_response(self.request('/test'),
                                            http.INTERNAL_SERVER_ERROR)

    @inlineCallbacks
    def test_api_dashboard_creation(self):
        yield self.assert_json_response(
            self.request('/api/dashboards', method='POST', data=json.dumps({
                'name': 'dashboard-3',
                'title': 'Dashboard 3',
                'share_id': 'dashboard-3-share-id',
            })), code=http.CREATED, data={'name': 'dashboard-3'})

        self.assertEqual(
            self.server.get_dashboard('dashboard-3').title, 'Dashboard 3')

    def test_api_dashboard_creation_for_unnamed_dashboards(self):
        return self.assert_unhappy_response(
            self.request('/api/dashboards', method='POST', data=json.dumps({
                'title': 'Dashboard 3',
                'share_id': 'dashboard-3-share-id',
            })), code=http.BAD_REQUEST)

    def test_api_dashboard_creation_for_already_existing_dashboards(self):
        return self.assert_unhappy_response(
            self.request('/api/dashboards', method='POST', data=json.dumps({
                'name': 'dashboard-1',
            })), code=http.BAD_REQUEST)

    def test_api_widget_details_retrieval(self):
        return self.assert_json_response(
            self.request('/api/widgets/dashboard-1/widget-1'), {
                'title': 'Widget 1',
                'type': 'dynamic_toy'
            })

    def test_api_widget_details_retrieval_for_nonexistent_dashboard(self):
        return self.assert_unhappy_response(
            self.request('/api/widgets/bad-dashboard/widget-1'),
            http.NOT_FOUND)

    def test_api_widget_details_retrieval_for_nonexistent_widget(self):
        return self.assert_unhappy_response(
            self.request('/api/widgets/dashboard-1/bad-widget'),
            http.NOT_FOUND)

    def test_api_widget_snapshot_retrieval(self):
        return self.assert_json_response(
            self.request('/api/widgets/dashboard-1/widget-1/snapshot'),
            ['widget-1'])

    def test_api_widget_snapshot_retrieval_for_nonexistent_dashboard(self):
        return self.assert_unhappy_response(
            self.request('/api/widgets/bad-dashboard/widget-1/snapshot'),
            http.NOT_FOUND)

    def test_api_widget_snapshot_retrieval_for_nonexistent_widget(self):
        return self.assert_unhappy_response(
            self.request('/api/widgets/dashboard-1/bad-widget/snapshot'),
            http.NOT_FOUND)

    def test_api_widget_snapshot_retrieval_for_static_widgets(self):
        return self.assert_unhappy_response(
            self.request('/api/widgets/dashboard-1/widget-2/snapshot'),
            http.BAD_REQUEST)


class DashboardIndexListItemTestCase(unittest.TestCase):
    def test_from_dashboard(self):
        """
        Should create a dashboard index list item from a dashboard instance.
        """
        dashboard = mk_dashboard(share_id='test-share-id')
        item = DashboardIndexListItem.from_dashboard(dashboard)

        self.assertEqual(item.url, '/some-dashboard')
        self.assertEqual(item.title, 'Some Dashboard')

        expected_shared_url = '/shared/test-share-id'
        self.assertEqual(item.shared_url_tag.tagName, 'a')
        self.assertEqual(item.shared_url_tag.children[0], expected_shared_url)
        self.assertEqual(item.shared_url_tag.attributes['href'],
                         expected_shared_url)

    def test_from_dashboard_for_no_share_id(self):
        """
        Should set the dashboard index list item's shared_url tag to an empty
        string if the dashboard does not have a share id.
        """
        item = DashboardIndexListItem.from_dashboard(mk_dashboard())
        self.assertEqual(item.shared_url_tag, '')
