"""Tests for diamondash's server"""

from os import path
from pkg_resources import resource_filename

from mock import Mock
from twisted.trial import unittest

from diamondash import utils
from diamondash import server
from diamondash.widgets.widget import Widget
from diamondash.dashboard import Dashboard
from diamondash.server import DiamondashServer, DashboardIndexListItem

_test_data_dir = resource_filename(__name__, 'test_server_data/')


class StubbedDashboard(Dashboard):
    def add_widget(self, widget):
        self.widgets.append(widget)

    @classmethod
    def dashboards_from_dir(cls, dashboards_dir, defaults=None):
        return ['fake-dashboards']


class ToyWidget(Widget):
    def handle_render_request(self, request):
        return '%s -- handled by %s' % (request, self.name)


class ServerTestCase(unittest.TestCase):

    def test_handle_render_request(self):
        """
        Should route the render request to the appropriate widget on the
        appropropriate dashboard.
        """
        widget = ToyWidget(name='test-widget', title='title', client_config={},
                           width=2)
        dashboard = mk_dashboard(widgets=[widget])
        dashboard.get_widget = Mock(return_value=widget)

        dd_server = DiamondashServer([], None)
        dd_server.dashboards_by_name['some-dashboard'] = dashboard
        server.server = dd_server

        result = server.handle_render_request(
            'fake-render-request', 'some-dashboard', 'test-widget')
        self.assertEqual(
            result, "fake-render-request -- handled by test-widget")

    def test_handle_render_for_bad_dashboard_request(self):
        """
        Should return an empty JSON object if the dashboard does not exist.
        """
        dd_server = DiamondashServer([], None)
        server.server = dd_server

        result = server.handle_render_request(
            'fake-render-request', 'some-dashboard', 'test-widget')
        self.assertEqual(result, "{}")

    def test_handle_render_for_bad_widget_request(self):
        """
        Should return an empty JSON object if the widget does not exist.
        """
        dashboard = mk_dashboard()
        dashboard.get_widget = Mock(return_value=None)

        dd_server = DiamondashServer([], None)
        dd_server.dashboards_by_name['some-dashboard'] = dashboard
        server.server = dd_server

        result = server.handle_render_request(
            'fake-render-request', 'some-dashboard', 'test-widget')
        self.assertEqual(result, "{}")


class StubbedDiamondashServer(DiamondashServer):
    ROOT_RESOURCE_DIR = _test_data_dir

    def add_dashboard(self, dashboard):
        self.dashboards.append(dashboard)


class DiamondashServerTestCase(unittest.TestCase):
    def setUp(self):
        self.patch(StubbedDiamondashServer, 'create_resources',
                   staticmethod(lambda *a, **kw: 'created-resources'))

        stubbed_from_config_file = staticmethod(
            lambda filepath, class_defaults: (filepath, class_defaults))
        self.patch(Dashboard, 'from_config_file', stubbed_from_config_file)

    def test_from_config_dir(self):
        """Should create the server from a configuration directory."""
        config_dir = path.join(_test_data_dir, 'etc')
        dd_server = StubbedDiamondashServer.from_config_dir(config_dir)

        expected_class_defaults = {
            'module.path.to.some.Class': {
                'foo': 'bar',
                'lerp': 'larp'
            }
        }
        dashboard_path = path.join(config_dir, 'dashboards')
        expected_dashboard1_path = path.join(dashboard_path, 'dashboard1.yml')
        expected_dashboard2_path = path.join(dashboard_path, 'dashboard2.yml')

        self.assertEqual(
            dd_server.dashboards,
            [(expected_dashboard1_path, expected_class_defaults),
             (expected_dashboard2_path, expected_class_defaults)])
        self.assertEqual(dd_server.resources, 'created-resources')

    def test_add_dashboard(self):
        """Should add a dashboard to the server."""
        def stubbed_index_add_dashboard(dashboard):
            stubbed_index_add_dashboard.called = True

        stubbed_index_add_dashboard.called = False

        dd_server = DiamondashServer([], None)
        dd_server.index.add_dashboard = stubbed_index_add_dashboard
        dashboard = mk_dashboard(name='some-dashboard',
                                 share_id='some-share-id')

        dd_server.add_dashboard(dashboard)
        self.assertEqual(dd_server.dashboards[-1], dashboard)
        self.assertEqual(
            dd_server.dashboards_by_name['some-dashboard'], dashboard)
        self.assertEqual(
            dd_server.dashboards_by_share_id['some-share-id'], dashboard)
        self.assertTrue(stubbed_index_add_dashboard.called)


class StubbedDashboardIndexListItem(DashboardIndexListItem):
    def __init__(self, title, url, shared_url_tag):
        self.title = title
        self.url = url
        self.shared_url_tag = shared_url_tag


class DashboardIndexListItemTestCase(unittest.TestCase):
    def test_from_dashboard(self):
        """
        Should create a dashboard index list item from a dashboard instance.
        """
        dashboard = mk_dashboard(share_id='test-share-id')
        item = StubbedDashboardIndexListItem.from_dashboard(dashboard)

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
        item = StubbedDashboardIndexListItem.from_dashboard(mk_dashboard())
        self.assertEqual(item.shared_url_tag, '')


def mk_dashboard(**kwargs):
    kwargs = utils.setdefaults(kwargs, {
        'name': 'some-dashboard',
        'title': 'Some Dashboard',
        'widgets': [],
        'client_config': {},
    })
    return StubbedDashboard(**kwargs)
