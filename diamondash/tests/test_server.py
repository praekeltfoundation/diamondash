"""Tests for diamondash's server"""

import json
from os import path
from pkg_resources import resource_filename

from twisted.trial import unittest
from twisted.internet.defer import maybeDeferred

from diamondash import utils
from diamondash.widgets.widget import Widget
from diamondash.dashboard import Dashboard
from diamondash.server import DiamondashServer, DashboardIndexListItem

_test_data_dir = resource_filename(__name__, 'test_server_data/')


class StubbedDashboard(Dashboard):
    def add_widget(self, widget):
        self.widgets.append(widget)
        self.widgets_by_name[widget.name] = widget

    @classmethod
    def dashboards_from_dir(cls, dashboards_dir, defaults=None):
        return ['fake-dashboards']


def mk_dashboard(**kwargs):
    kwargs = utils.update_dict({
        'name': 'some-dashboard',
        'title': 'Some Dashboard',
        'widgets': [],
        'client_config': {},
    }, kwargs)
    return StubbedDashboard(**kwargs)


class ToyWidget(Widget):
    def get_data(self):
        return [self.name]


class StubbedDiamondashServer(DiamondashServer):
    ROOT_RESOURCE_DIR = _test_data_dir

    def add_dashboard(self, dashboard):
        self.dashboards.append(dashboard)


class DiamondashServerTestCase(unittest.TestCase):
    def setUp(self):
        self.patch(StubbedDiamondashServer, 'create_resources',
                   staticmethod(lambda *a, **kw: 'created-resources'))

        self.patch(Dashboard, 'from_config_file', staticmethod(
            lambda filepath, class_defaults: (filepath, class_defaults)))

        widget = self.mk_toy_widget()
        dashboard = mk_dashboard(widgets=[widget])
        self.server = DiamondashServer([], None)
        self.server.add_dashboard(dashboard)

    def mk_toy_widget(self, **kwargs):
        return ToyWidget(**utils.update_dict({
            'name': 'some-widget',
            'title': 'title',
            'client_config': {},
            'width': 2
        }, kwargs))

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

    def assert_widget_data_retrieval(self, dashboard_name, widget_name,
                                     expected):
        d = maybeDeferred(self.server.get_widget_data, 'fake-req',
                          dashboard_name, widget_name)

        def assert_widget_data_retrieval(result):
            self.assertEqual(result, expected)
        d.addCallback(assert_widget_data_retrieval)

        return d

    def test_widget_data_retrieval(self):
        return self.assert_widget_data_retrieval(
            'some-dashboard', 'some-widget', json.dumps(['some-widget']))

    def test_widget_data_retrieval_for_nonexistent_dashboard(self):
        return self.assert_widget_data_retrieval(
            'bad-dashboard', 'some-widget', "{}")

    def test_widget_data_retrieval_for_nonexistent_widget(self):
        return self.assert_widget_data_retrieval(
            'some-dashboard', 'bad-widget', "{}")


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
