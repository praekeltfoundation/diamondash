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

    def mk_request(self, path, **kwargs):
        d = utils.http_request("%s%s" % (self.url, path), **kwargs)
        return d

    def assert_response(self, response, body, code=http.OK, headers={}):
        self.assertEqual(response['status'], str(code))
        self.assertEqual(response['body'], body)
        for field, value in headers.iteritems():
            self.assertEqual(response['headers'][field], value)

    def assert_json_response(self, response, data, code=http.OK, headers={}):
        headers.update({'content-type': ['application/json']})
        return self.assert_response(response, json.dumps(data), code, headers)

    def assert_unhappy_response(self, failure, code):
        failure.trap(web.error.Error)
        self.assertEqual(failure.value.status, str(code))

    def assert_rendering(self, response, expected_element):
        d = flattenString(None, expected_element)
        d.addCallback(lambda body: self.assert_response(response, body))
        return d

    def test_index_rendering(self):
        d = self.mk_request('/')
        d.addCallback(self.assert_response,  'mock-index')
        return d

    def test_static_resource_rendering(self):
        def assert_static_rendering(path, expected):
            d = self.mk_request(path)
            d.addCallback(self.assert_response,  expected)
            return d

        return gatherResults([
            assert_static_rendering('/js/a.js', 'mock-a.js'),
            assert_static_rendering('/js/b.js', 'mock-b.js'),
            assert_static_rendering('/shared/js/a.js', 'mock-a.js'),
            assert_static_rendering('/shared/js/b.js', 'mock-b.js'),
            assert_static_rendering('/css/a.css', 'mock-a.css'),
            assert_static_rendering('/css/b.css', 'mock-b.css'),
            assert_static_rendering('/shared/css/a.css', 'mock-a.css'),
            assert_static_rendering('/shared/css/b.css', 'mock-b.css'),
        ])

    def test_dashboard_rendering(self):
        d = self.mk_request('/dashboard-1')
        d.addCallback(self.assert_rendering, DashboardPage(self.dashboard1))
        return d

    def test_dashboard_rendering_for_non_existent_dashboards(self):
        d = self.mk_request('/dashboard-3')
        d.addErrback(self.assert_unhappy_response, http.NOT_FOUND)
        return d

    def test_shared_dashboard_rendering(self):
        d = self.mk_request('/shared/dashboard-1-share-id')
        d.addCallback(self.assert_rendering, DashboardPage(self.dashboard1))
        return d

    def test_shared_dashboard_rendering_for_non_existent_dashboards(self):
        d = self.mk_request('/shared/dashboard-3-share-id')
        d.addErrback(self.assert_unhappy_response, http.NOT_FOUND)
        return d

    def test_widget_details_retrieval(self):
        d = self.mk_request('/api/widgets/dashboard-1/widget-1')
        d.addCallback(self.assert_json_response, {
            'title': 'Widget 1',
            'type': 'dynamic_toy'
        })
        return d

    def test_widget_details_retrieval_for_nonexistent_dashboard(self):
        d = self.mk_request('/api/widgets/bad-dashboard/widget-1')
        d.addErrback(self.assert_unhappy_response, http.NOT_FOUND)
        return d

    def test_widget_details_retrieval_for_nonexistent_widget(self):
        d = self.mk_request('/api/widgets/dashboard-1/bad-widget')
        d.addErrback(self.assert_unhappy_response, http.NOT_FOUND)
        return d

    def test_widget_snapshot_retrieval(self):
        d = self.mk_request('/api/widgets/dashboard-1/widget-1/snapshot')
        d.addCallback(self.assert_json_response, ['widget-1'])
        return d

    def test_widget_snapshot_retrieval_for_nonexistent_dashboard(self):
        d = self.mk_request('/api/widgets/bad-dashboard/widget-1/snapshot')
        d.addErrback(self.assert_unhappy_response, http.NOT_FOUND)
        return d

    def test_widget_snapshot_retrieval_for_nonexistent_widget(self):
        d = self.mk_request('/api/widgets/dashboard-1/bad-widget/snapshot')
        d.addErrback(self.assert_unhappy_response, http.NOT_FOUND)
        return d

    def test_widget_snapshot_retrieval_for_static_widgets(self):
        d = self.mk_request('/api/widgets/dashboard-1/widget-2/snapshot')
        d.addErrback(self.assert_unhappy_response, http.BAD_REQUEST)
        return d


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
