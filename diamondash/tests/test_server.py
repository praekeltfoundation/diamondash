"""Tests for diamondash's server"""

import json

from twisted import web
from twisted.web import http
from twisted.trial import unittest
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, gatherResults
from twisted.python.failure import Failure
from twisted.web.template import flattenString

from diamondash import utils, ConfigError
from diamondash.widgets.widget import Widget
from diamondash.widgets.dynamic import DynamicWidget
from diamondash.dashboard import Dashboard, DashboardPage
from diamondash.server import DiamondashServer, Index, DashboardIndexListItem


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


class MockIndex(MockLeafResource, Index):
    def __init__(self, dashboards=[]):
        MockLeafResource.__init__(self, 'mock-index')
        Index.__init__(self, dashboards)


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

    @staticmethod
    def raise_error(error_class, *args, **kwargs):
        raise error_class(*args, **kwargs)

    def mock_dashboard_config_error(self):
        self.patch(Dashboard, 'from_config', classmethod(
           lambda *a, **kw: self.raise_error(ConfigError)))

    def assert_response(self, response, body, code=http.OK, headers={}):
        self.assertEqual(response['status'], str(code))
        self.assertEqual(response['body'], body)
        for field, value in headers.iteritems():
            self.assertEqual(response['headers'][field], value)

    def assert_json_response(self, d, data, code=http.OK, headers={}):
        headers.update({'content-type': ['application/json']})
        self.assert_response(d, json.dumps(data), code, headers)

    def assert_unhappy_response(self, failure, code):
        if not isinstance(failure, Failure):
            self.fail()  # fail the test if a failure didn't occur
        failure.trap(web.error.Error)
        self.assertEqual(failure.value.status, str(code))

    def assert_rendering(self, response, expected_element):
        d = flattenString(None, expected_element)
        d.addCallback(lambda body: self.assert_response(response, body))
        return d

    def test_index_rendering(self):
        d = self.request('/')
        d.addCallback(self.assert_response, 'mock-index')
        return d

    def test_static_resource_rendering(self):
        def request_and_assert(path, expected):
            d = self.request(path)
            d.addCallback(self.assert_response, expected)
            return d

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
        d = self.request('/dashboard-1')
        d.addCallback(self.assert_rendering, DashboardPage(self.dashboard1))
        return d

    def test_dashboard_rendering_for_non_existent_dashboards(self):
        d = self.request('/dashboard-3')
        d.addBoth(self.assert_unhappy_response, http.NOT_FOUND)
        return d

    def test_shared_dashboard_rendering(self):
        d = self.request('/shared/dashboard-1-share-id')
        d.addCallback(self.assert_rendering, DashboardPage(self.dashboard1))
        return d

    def test_shared_dashboard_rendering_for_non_existent_dashboards(self):
        d = self.request('/shared/dashboard-3-share-id')
        d.addBoth(self.assert_unhappy_response, http.NOT_FOUND)
        return d

    def test_unhandled_api_get_error_trapping(self):
        @self.server.app.route('/test')
        def api_method(slf, request):
            slf.api_get(request, lambda: self.raise_error(MockError))

        d = self.request('/test')
        d.addBoth(self.assert_unhappy_response, http.INTERNAL_SERVER_ERROR)
        return d

    def test_api_dashboard_details_retrieval(self):
        d = self.request('/api/dashboards/dashboard-1')
        d.addCallback(self.assert_json_response, {
            'title': 'Dashboard 1',
            'share_id': 'dashboard-1-share-id',
            'widgets': [
                {
                    'title': 'Widget 1',
                    'type': 'dynamic_toy'
                },
                {
                    'title': 'Widget 2',
                    'type': 'static_toy'
                },
            ]
        })
        return d

    def test_api_dashboard_creation(self):
        d = self.request('/api/dashboards', method='POST', data=json.dumps({
            'name': 'dashboard-3',
            'title': 'Dashboard 3',
            'share_id': 'dashboard-3-share-id',
        }))

        d.addCallback(self.assert_json_response, code=http.CREATED,
                      data={'name': 'dashboard-3', 'status': 'CREATED'})
        d.addCallback(lambda _: self.assertEqual(
            self.server.get_dashboard('dashboard-3').title, 'Dashboard 3'))
        return d

    def test_api_dashboard_creation_for_unnamed_dashboards(self):
        d = self.request('/api/dashboards', method='POST', data=json.dumps({
            'title': 'Dashboard 3',
            'share_id': 'dashboard-3-share-id',
        }))
        d.addBoth(self.assert_unhappy_response, code=http.BAD_REQUEST)
        return d

    def test_api_dashboard_creation_for_already_existing_dashboards(self):
        d = self.request('/api/dashboards', method='POST',
                         data=json.dumps({'name': 'dashboard-1'}))
        d.addBoth(self.assert_unhappy_response, code=http.BAD_REQUEST)
        return d

    def test_api_dashboard_creation_for_config_error_handling(self):
        self.mock_dashboard_config_error()
        d = self.request('/api/dashboards', method='POST',
                         data=json.dumps({'name': 'some-dashboard'}))
        d.addBoth(self.assert_unhappy_response, http.BAD_REQUEST)
        return d

    def test_api_dashboard_creation_for_bad_config_object_handling(self):
        def request_and_assert(path, data):
            d = self.request(path, method='POST', data=data)
            d.addBoth(self.assert_unhappy_response, http.BAD_REQUEST)
            return d

        return gatherResults([
            request_and_assert('/api/dashboards', ""),
            request_and_assert('/api/dashboards', "[]"),
        ])

    def test_api_dashboard_replacement_for_new_dashboards(self):
        d = self.request('/api/dashboards/dashboard-3', data=json.dumps({
            'title': 'Dashboard 3',
            'share_id': 'dashboard-3-share-id',
        }), method='PUT')

        d.addCallback(self.assert_json_response, {'name': 'dashboard-3'})
        d.addCallback(lambda _: self.assertEqual(
            self.server.get_dashboard('dashboard-3').title, 'Dashboard 3'))
        return d

    def test_api_dashboard_replacement_for_already_existing_dashboards(self):
        d = self.request('/api/dashboards/dashboard-1', data=json.dumps({
            'title': 'New Dashboard 1',
            'share_id': 'dashboard-1-share-id',
        }), method='PUT')

        d.addCallback(self.assert_json_response, {'name': 'dashboard-1'})
        d.addCallback(lambda _: self.assertEqual(
            self.server.get_dashboard('dashboard-1').title, 'New Dashboard 1'))
        return d

    def test_api_dashboard_replacement_for_config_error_handling(self):
        self.mock_dashboard_config_error()
        d = self.request(
            '/api/dashboards/dashboard-1', method='PUT', data="{}")
        d.addBoth(self.assert_unhappy_response, http.BAD_REQUEST)
        return d

    def test_api_dashboard_replacement_for_bad_config_object_handling(self):
        def request_and_assert(path, data):
            d = self.request(path, method='PUT', data=data)
            d.addBoth(self.assert_unhappy_response, http.BAD_REQUEST)
            return d

        return gatherResults([
            request_and_assert('/api/dashboards/dashboard-1', ""),
            request_and_assert('/api/dashboards/dashboard-1', "[]"),
        ])

    def test_api_dashboard_removal(self):
        d = self.request('/api/dashboards/dashboard-1', method='DELETE')
        d.addCallback(self.assert_json_response,
                      data={'name': 'dashboard-1', 'status': 'DELETED'})
        d.addCallback(lambda _: self.assertFalse(
            self.server.has_dashboard('dashboard-1')))
        d.addCallback(lambda _: self.assertFalse(
            self.server.index.has_dashboard('dashboard-1')))
        return d

    def test_api_dashboard_removal_for_nonexistent_dashboards(self):
        d = self.request('/api/dashboards/dashboard-3', method='DELETE')
        d.addBoth(self.assert_unhappy_response, http.NOT_FOUND)
        return d

    def test_api_widget_details_retrieval(self):
        d = self.request('/api/widgets/dashboard-1/widget-1')
        d.addCallback(self.assert_json_response, {
            'title': 'Widget 1',
            'type': 'dynamic_toy'
        })
        return d

    def test_api_widget_details_retrieval_for_nonexistent_dashboard(self):
        d = self.request('/api/widgets/bad-dashboard/widget-1')
        d.addBoth(self.assert_unhappy_response, http.NOT_FOUND)
        return d

    def test_api_widget_details_retrieval_for_nonexistent_widget(self):
        d = self.request('/api/widgets/dashboard-1/bad-widget')
        d.addBoth(self.assert_unhappy_response, http.NOT_FOUND)
        return d

    def test_api_widget_snapshot_retrieval(self):
        d = self.request('/api/widgets/dashboard-1/widget-1/snapshot')
        d.addCallback(self.assert_json_response, ['widget-1'])
        return d

    def test_api_widget_snapshot_retrieval_for_nonexistent_dashboard(self):
        d = self.request('/api/widgets/bad-dashboard/widget-1/snapshot')
        d.addBoth(self.assert_unhappy_response, http.NOT_FOUND)
        return d

    def test_api_widget_snapshot_retrieval_for_nonexistent_widget(self):
        d = self.request('/api/widgets/dashboard-1/bad-widget/snapshot')
        d.addBoth(self.assert_unhappy_response, http.NOT_FOUND)
        return d

    def test_api_widget_snapshot_retrieval_for_static_widgets(self):
        d = self.request('/api/widgets/dashboard-1/widget-2/snapshot')
        d.addBoth(self.assert_unhappy_response, http.BAD_REQUEST)
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
