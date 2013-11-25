"""Tests for diamondash's server"""

import os
import json

from twisted import web
from twisted.web import http
from twisted.trial import unittest
from twisted.web.server import Site
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, gatherResults
from twisted.python.failure import Failure
from twisted.web.template import flattenString

from diamondash import utils
from diamondash.config import ConfigError
from diamondash.widgets.widget import WidgetConfig
from diamondash.dashboard import Dashboard, DashboardConfig, DashboardPage
from diamondash.server import (
    DiamondashConfig, DiamondashServer, Index, DashboardIndexListItem)


class MockError(Exception):
    """I am fake"""


def mk_dashboard_config_data(**overrides):
    return utils.add_dicts({
        'name': 'Some Dashboard',
        'request_interval': '2s',
        'share_id': 'some-share-id',
        'widgets': [{
            'name': 'Widget 1',
            'type': 'diamondash.tests.utils.ToyDynamicWidget',
        }, {
            'name': 'Widget 2',
            'type': 'diamondash.widgets.widget.Widget',
        }],
    }, overrides)


def mk_server_config_data(**overrides):
    return utils.add_dicts({
        'backend': {
            'type': 'diamondash.tests.utils.ToyBackend',
            'url': 'http://127.0.0.1:3000',
        },
        'dashboards': [
            mk_dashboard_config_data(
                name='Dashboard 1',
                share_id='dashboard-1-share-id'),
            mk_dashboard_config_data(
                name='Dashboard 2',
                share_id='dashboard-2-share-id')]
    }, overrides)


class DiamondashConfigTestCase(unittest.TestCase):
    def test_from_dir(self):
        dirname = os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'etc')

        config = DiamondashConfig.from_dir(dirname)

        dashboard1_config, dashboard2_config = config['dashboards']

        self.assertTrue(isinstance(dashboard1_config, DashboardConfig))
        self.assertEqual(dashboard1_config['name'], 'dashboard-1')
        self.assertEqual(dashboard1_config['title'], 'Dashboard 1')

        widget1_config, = dashboard1_config['widgets']
        self.assertTrue(isinstance(widget1_config, WidgetConfig))
        self.assertEqual(widget1_config['name'], 'dashboard-1-widget-1')
        self.assertEqual(widget1_config['title'], 'Dashboard 1 Widget 1')
        self.assertEqual(
            widget1_config['backend']['url'],
            'http://127.0.0.1:8118')

        self.assertTrue(isinstance(dashboard2_config, DashboardConfig))
        self.assertEqual(dashboard2_config['name'], 'dashboard-2')
        self.assertEqual(dashboard2_config['title'], 'Dashboard 2')

        widget1_config, = dashboard2_config['widgets']
        self.assertTrue(isinstance(widget1_config, WidgetConfig))
        self.assertEqual(widget1_config['name'], 'dashboard-2-widget-1')
        self.assertEqual(widget1_config['title'], 'Dashboard 2 Widget 1')
        self.assertEqual(
            widget1_config['backend']['url'],
            'http://127.0.0.1:7118')


class DiamondashServerTestCase(unittest.TestCase):
    def setUp(self):
        config = DiamondashConfig(mk_server_config_data())
        self.server = DiamondashServer(config)
        self.dashboard1 = self.server.get_dashboard('dashboard-1')
        self.dashboard2 = self.server.get_dashboard('dashboard-2')
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

    def request(self, path, **kwargs):
        d = utils.http_request("%s%s" % (self.url, path), **kwargs)
        return d

    @staticmethod
    def raise_error(error_class, *args, **kwargs):
        raise error_class(*args, **kwargs)

    def mock_dashboard_config_error(self):
        self.patch(DashboardConfig, 'parse', classmethod(
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
        d.addCallback(
            self.assert_rendering,
            Index([self.dashboard1, self.dashboard2]))
        return d

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
        d.addCallback(
            self.assert_rendering,
            DashboardPage(self.dashboard1, shared=True))
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
        d.addCallback(self.assert_json_response, self.dashboard1.get_details())
        return d

    def test_api_dashboard_creation(self):
        data = mk_dashboard_config_data(name='Dashboard 3')

        d = self.request(
            '/api/dashboards',
            method='POST',
            data=json.dumps(data))

        def assert_response(response):
            dashboard = self.server.get_dashboard('dashboard-3')
            backend = dashboard.get_widget('widget-1').config['backend']

            self.assertEqual(
                backend['url'],
                'http://127.0.0.1:3000')

            self.assertEqual(
                backend['type'],
                'diamondash.tests.utils.ToyBackend')

            self.assert_json_response(
                response,
                code=http.CREATED,
                data={
                    'success': True,
                    'data': dashboard.get_details()
                })

        d.addCallback(assert_response)
        return d

    def test_api_dashboard_creation_for_unnamed_dashboards(self):
        data = mk_dashboard_config_data(name='Dashboard 3')
        del data['name']

        d = self.request(
            '/api/dashboards',
            method='POST',
            data=json.dumps(data))

        d.addBoth(self.assert_unhappy_response, code=http.BAD_REQUEST)
        return d

    def test_api_dashboard_creation_for_already_existing_dashboards(self):
        d = self.request(
            '/api/dashboards',
            method='POST',
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
        data = mk_dashboard_config_data(name='dashboard-3')

        d = self.request(
            '/api/dashboards',
            data=json.dumps(data),
            method='PUT')

        def assert_response(response):
            dashboard = self.server.get_dashboard('dashboard-3')
            backend = dashboard.get_widget('widget-1').config['backend']

            self.assertEqual(
                backend['url'],
                'http://127.0.0.1:3000')

            self.assertEqual(
                backend['type'],
                'diamondash.tests.utils.ToyBackend')

            self.assert_json_response(
                response,
                code=http.OK,
                data={
                    'success': True,
                    'data': dashboard.get_details()
                })

        d.addCallback(assert_response)
        return d

    def test_api_dashboard_replacement_for_already_existing_dashboards(self):
        data = mk_dashboard_config_data(name='dashboard-1')

        d = self.request(
            '/api/dashboards',
            method='PUT',
            data=json.dumps(data))

        def assert_response(response):
            dashboard = self.server.get_dashboard('dashboard-1')
            backend = dashboard.get_widget('widget-1').config['backend']

            self.assertEqual(
                backend['url'],
                'http://127.0.0.1:3000')

            self.assertEqual(
                backend['type'],
                'diamondash.tests.utils.ToyBackend')

            self.assert_json_response(
                response,
                code=http.OK,
                data={
                    'success': True,
                    'data': dashboard.get_details()
                })

        d.addCallback(assert_response)
        return d

    def test_api_dashboard_replacement_for_config_error_handling(self):
        self.mock_dashboard_config_error()
        d = self.request(
            '/api/dashboards', method='PUT', data="{}")
        d.addBoth(self.assert_unhappy_response, http.BAD_REQUEST)
        return d

    def test_api_dashboard_replacement_for_bad_config_object_handling(self):
        def request_and_assert(path, data):
            d = self.request(path, method='PUT', data=data)
            d.addBoth(self.assert_unhappy_response, http.BAD_REQUEST)
            return d

        return gatherResults([
            request_and_assert('/api/dashboards', ""),
            request_and_assert('/api/dashboards', "[]"),
        ])

    def test_api_dashboard_removal(self):
        d = self.request('/api/dashboards/dashboard-1', method='DELETE')

        def assert_response(response):
            self.assert_json_response(response, {
                'success': True,
                'data': None,
            })

            self.assertFalse(self.server.has_dashboard('dashboard-1'))
            self.assertFalse(self.server.index.has_dashboard('dashboard-1'))

        d.addCallback(assert_response)
        return d

    def test_api_dashboard_removal_for_nonexistent_dashboards(self):
        d = self.request('/api/dashboards/dashboard-3', method='DELETE')
        d.addBoth(self.assert_unhappy_response, http.NOT_FOUND)
        return d

    def test_api_widget_details_retrieval(self):
        d = self.request('/api/widgets/dashboard-1/widget-1')
        d.addCallback(
            self.assert_json_response,
            self.dashboard1.get_widget('widget-1').get_details())
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

    def test_add_dashboard(self):
        """Should add a dashboard to the server."""
        config = DashboardConfig(mk_dashboard_config_data())
        self.server.add_dashboard(config)

        self.assertEqual(
            self.server.dashboards_by_name['some-dashboard'].config,
            config)
        self.assertEqual(
            self.server.dashboards_by_share_id['some-share-id'].config,
            config)


class DashboardIndexListItemTestCase(unittest.TestCase):
    def test_from_dashboard(self):
        """
        Should create a dashboard index list item from a dashboard instance.
        """
        data = mk_dashboard_config_data(share_id='test-share-id')
        dashboard = Dashboard(DashboardConfig(data))
        item = DashboardIndexListItem.from_dashboard(dashboard)

        self.assertEqual(item.url, '/some-dashboard')
        self.assertEqual(item.title, 'Some Dashboard')

        self.assertEqual(item.shared_url_tag.tagName, 'a')

        self.assertEqual(
            item.shared_url_tag.children[0],
            '/shared/test-share-id')

        self.assertEqual(
            item.shared_url_tag.attributes['href'],
            '/shared/test-share-id')

    def test_from_dashboard_for_no_share_id(self):
        """
        Should set the dashboard index list item's shared_url tag to an empty
        string if the dashboard does not have a share id.
        """
        data = mk_dashboard_config_data(share_id='test-share-id')
        del data['share_id']
        dashboard = Dashboard(DashboardConfig(data))

        item = DashboardIndexListItem.from_dashboard(dashboard)
        self.assertEqual(item.shared_url_tag, '')
