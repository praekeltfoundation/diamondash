"""Tests for diamondash's server"""

from os import path
from pkg_resources import resource_filename

from mock import patch, Mock
from twisted.trial import unittest
from twisted.web.resource import NoResource
from twisted.python.filepath import FilePath

from diamondash import server
from diamondash.widgets.widget import Widget
from diamondash.dashboard import Dashboard
from diamondash.server import DiamondashServer, Index, DashboardIndexListItem

_test_data_dir = resource_filename(__name__, 'test_server_data/')


class StubbedDashboard(Dashboard):
    def __init__(self, name=None, title=None, widgets=None,
                 client_config=None, share_id=None):
        self.name = name
        self.title = title
        self.widgets = widgets
        self.client_config = client_config
        self.share_id = share_id


class ToyWidget(Widget):
    def __init__(self, name):
        self.name = name

    def handle_render_request(self, request):
        return '%s -- handled by %s' % (request, self.name)


class ServerTestCase(unittest.TestCase):
    def test_handle_render_request(self):
        """
        Should route the render request to the appropriate widget on the
        appropropriate dashboard.
        """
        widget = ToyWidget('test-widget')
        dashboard = StubbedDashboard(name='test-dashboard')
        dashboard.get_widget = Mock(return_value=widget)

        dd_server = DiamondashServer([], None, {})
        dd_server.dashboards_by_name['test-dashboard'] = dashboard
        server.server = dd_server

        result = server.handle_render_request(
            'fake-render-request', 'test-dashboard', 'test-widget')
        self.assertEqual(
            result, "fake-render-request -- handled by test-widget")

    def test_handle_render_for_bad_dashboard_request(self):
        """
        Should return an empty JSON object if the dashboard does not exist.
        """
        dd_server = DiamondashServer([], None, {})
        server.server = dd_server

        result = server.handle_render_request(
            'fake-render-request', 'test-dashboard', 'test-widget')
        self.assertEqual(result, "{}")

    def test_handle_render_for_bad_widget_request(self):
        """
        Should return an empty JSON object if the widget does not exist.
        """
        dashboard = StubbedDashboard(name='test-dashboard')
        dashboard.get_widget = Mock(return_value=None)

        dd_server = DiamondashServer([], None, {})
        dd_server.dashboards_by_name['test-dashboard'] = dashboard
        server.server = dd_server

        result = server.handle_render_request(
            'fake-render-request', 'test-dashboard', 'test-widget')
        self.assertEqual(result, "{}")


class ServerUtilsTestCase(unittest.TestCase):
    def test_create_resource_from_path(self):
        """
        Should create a resource containing all the files and dirs that match
        the pathname.
        """
        def assert_resources(pathname, expected_entities):
            pathname = path.join(_test_data_dir, pathname)
            res = server.create_resource_from_path(pathname)
            entities = res.listEntities()
            for entity, expected_entity in zip(entities, expected_entities):
                name, filepath = entity
                expected_name, expected_filepath = expected_entity
                expected_filepath = FilePath(
                    path.join(_test_data_dir, expected_filepath))

                self.assertEqual(name, expected_name)
                self.assertEqual(filepath, expected_filepath)

        assert_resources('widgets/a/*.js',
                         [('a-widget.js', 'widgets/a/a-widget.js')])

        assert_resources('widgets/b/*.py',
                         [('b_widget.py', 'widgets/b/b_widget.py')])


class StubbedDiamondashServer(DiamondashServer):
    ROOT_RESOURCE_DIR = _test_data_dir

    def __init__(self, dashboards, public_resources, widget_resources):
        self.dashboards = dashboards
        self.public_resources = public_resources
        self.widget_resources = widget_resources


class DiamondashServerTestCase(unittest.TestCase):

    @patch.object(server, 'create_resource_from_path')
    def test_create_widget_resources(self, mock_create_resource_from_path):
        """
        Should create the widget resources (javascripts and stylesheets) from
        files.
        """
        def stubbed_create_resource_from_path(pathname):
            return '%s -- created' % pathname

        mock_create_resource_from_path.side_effect = (
            stubbed_create_resource_from_path)

        widget_resources = StubbedDiamondashServer.create_widget_resources()
        widgets_dir = path.join(_test_data_dir, 'widgets')
        self.assertEqual(widget_resources, {
            'javascripts': {
                'a': '%s/a/*.js -- created' % widgets_dir,
                'b': '%s/b/*.js -- created' % widgets_dir,
            },
            'stylesheets': {
                'a': '%s/a/*.css -- created' % widgets_dir,
                'b': '%s/b/*.css -- created' % widgets_dir,
            },
        })

    def test_get_widget_resource(self):
        """
        Should return the resources corresponding to the passed in resource
        type and widget type.
        """
        widget_resources = {
            'resource-a': {'widget-1': 'a1-resources'}
        }
        dd_server = DiamondashServer([], None, widget_resources)

        result = dd_server.get_widget_resource('resource-a', 'widget-1')
        self.assertEqual(result, 'a1-resources')

    def test_get_widget_resource_for_bad_type_request(self):
        dd_server = DiamondashServer([], None, {})
        result = dd_server.get_widget_resource('resource-a', 'widget-1')
        self.assertTrue(isinstance(result, NoResource))

    @patch.object(StubbedDiamondashServer, 'create_public_resources')
    @patch.object(StubbedDiamondashServer, 'create_widget_resources')
    @patch.object(Dashboard, 'dashboards_from_dir')
    def test_from_config_dir(self, mock_dashboards_from_dir,
                             mock_create_widget_resources,
                             mock_create_public_resources):
        """Should create the server from a configuration directory."""

        mock_create_public_resources.return_value = 'fake-public-resources'
        mock_create_widget_resources.return_value = 'fake-widget-resources'
        mock_dashboards_from_dir.return_value = 'fake-dashboards'

        config_dir = path.join(_test_data_dir, 'etc')
        dd_server = StubbedDiamondashServer.from_config_dir(config_dir)

        expected_dashboards_dir = path.join(config_dir, 'dashboards')
        expected_dashboard_defaults = {
            'some_dashboard_default': 'mon mothma',
            'widget_defaults': {'some_widget_default': 'admiral ackbar'}
        }
        mock_dashboards_from_dir.assert_called_with(
            expected_dashboards_dir, expected_dashboard_defaults)

        self.assertEqual(dd_server.dashboards, 'fake-dashboards')
        self.assertEqual(dd_server.public_resources, 'fake-public-resources')
        self.assertEqual(dd_server.widget_resources, 'fake-widget-resources')

    def test_add_dashboard(self):
        """Should add a dashboard to the server."""
        def stubbed_index_add_dashboard(dashboard):
            stubbed_index_add_dashboard.called = True

        stubbed_index_add_dashboard.called = False

        dd_server = DiamondashServer([], None, {})
        dd_server.index.add_dashboard = stubbed_index_add_dashboard
        dashboard = StubbedDashboard(name='test-dashboard',
                                     share_id='test-share-id')

        dd_server.add_dashboard(dashboard)
        self.assertEqual(dd_server.dashboards[-1], dashboard)
        self.assertEqual(
            dd_server.dashboards_by_name['test-dashboard'], dashboard)
        self.assertEqual(
            dd_server.dashboards_by_share_id['test-share-id'], dashboard)
        self.assertTrue(stubbed_index_add_dashboard.called)


class StubbedDashboardIndexListItem(DashboardIndexListItem):
    def __init__(self, title, url, shared_url_tag):
        self.title = title
        self.url = url
        self.shared_url_tag = shared_url_tag


class IndexTestCase(unittest.TestCase):
    @patch.object(DashboardIndexListItem, 'from_dashboard')
    def test_add_dashboard(self, mock_from_dashboard):
        """
        Should add a dashboard list item to the index's dashboard list.
        """
        def stubbed_from_dashboard(dashboard):
            return 'created from: %s' % dashboard.name

        mock_from_dashboard.side_effect = stubbed_from_dashboard

        index = Index()
        dashboard = StubbedDashboard(name='test-dashboard')
        index.add_dashboard(dashboard)
        self.assertEqual(index.dashboard_list_items[0],
                         'created from: test-dashboard')


class DashboardIndexListItemTestCase(unittest.TestCase):
    def test_from_dashboard(self):
        """
        Should create a dashboard index list item from a dashboard instance.
        """
        dashboard = StubbedDashboard(name='test-dashboard',
                                     title='Test Dashboard',
                                     share_id='test-share-id')
        item = StubbedDashboardIndexListItem.from_dashboard(dashboard)

        self.assertEqual(item.url, '/test-dashboard')
        self.assertEqual(item.title, 'Test Dashboard')

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
        dashboard = StubbedDashboard(name='test-dashboard',
                                     title='Test Dashboard',
                                     share_id=None)
        item = StubbedDashboardIndexListItem.from_dashboard(dashboard)
        self.assertEqual(item.shared_url_tag, '')
