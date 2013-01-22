"""Tests for diamondash's dashboard"""

from pkg_resources import resource_filename

from mock import patch, Mock
from twisted.trial import unittest

from diamondash import utils
from diamondash.dashboard import Dashboard
from diamondash.widgets.widget import Widget
from diamondash.exceptions import ConfigError


class StubbedDashboard(Dashboard):
    LAYOUT_FUNCTIONS = ['layoutfn1', 'layoutfn2']

    def __init__(self, name, title, widgets, client_config, share_id):
        self.name = name
        self.title = title
        self.widgets = widgets
        self.client_config = client_config
        self.share_id = share_id


class ToyWidget(Widget):
    STYLESHEETS = ('toy/style.css',)
    JAVASCRIPTS = ('toy/toy-widget',)


class DashboardTestCase(unittest.TestCase):
    def test_new_row(self):
        """
        Should append an empty row and set the last row width to 0.
        """
        dashboard = Dashboard('test-dashboard', 'test dashboard', [], {})
        dashboard.rows = [[]]
        dashboard.last_row_width = 23
        dashboard._new_row()
        self.assertEqual(dashboard.rows, [[], []])
        self.assertEqual(dashboard.last_row_width, 0)

    def test_add_widget(self):
        """Should add a widget to the dashboard."""

        dashboard = Dashboard('test-dashboard', 'Test Dashboard', [], {})
        dashboard.WIDGET_STYLESHEETS_PATH = "/test/css/widgets/"
        dashboard.WIDGET_JAVASCRIPTS_PATH = "widgets/"

        widget = ToyWidget(name='toy', title='Toy',
                           client_config='toy_client_config', width=2)
        dashboard.add_widget(widget)

        self.assertEqual(dashboard.widgets_by_name['toy'], widget)
        self.assertEqual(dashboard.widgets[0], widget)
        self.assertEqual(dashboard.rows, [[widget]])
        self.assertEqual(dashboard.last_row_width, 2)
        self.assertEqual(dashboard.client_config['widgets'][0],
                         'toy_client_config')
        self.assertEqual(dashboard.stylesheets,
                         set(['/test/css/widgets/toy/style.css']))
        self.assertEqual(dashboard.javascripts,
                         set(['widgets/toy/toy-widget']))

    def test_add_widget_for_layout_fn(self):
        """
        Should call the appropriate layout function if the function's name is
        passed in as a 'widget'.
        """
        mock_layoutfn = Mock()
        dashboard = Dashboard('test-dashboard', 'Test Dashboard', [], {})
        dashboard.LAYOUT_FUNCTIONS = ['toy']
        dashboard.layoutfns = {'toy': mock_layoutfn}
        dashboard.add_widget('toy')
        self.assertTrue(mock_layoutfn.called)

    @patch.object(Widget, 'MAX_COLUMN_SPAN')
    def test_add_widget_for_new_row(self, mock_widget_max_column_span):
        """
        Should add a new row if there is no space for the widget being added on
        the current row.
        """
        dashboard = Dashboard('test-dashboard', 'Test Dashboard', [], {})
        dashboard._new_row = Mock()
        dashboard.last_row_width = 3

        widget = ToyWidget(name='toy', title='Toy',
                           client_config='toy_client_config', width=2)
        mock_widget_max_column_span.side_effect = 4

        dashboard.add_widget(widget)
        self.assertTrue(dashboard._new_row.called)
        self.assertEqual(dashboard.last_row_width, 2)

    @patch.object(Dashboard, 'from_config_file')
    def test_dashboards_from_dir(self, mock_from_config_file):
        """Should create a list of dashboards from a config dir."""

        def stubbed_from_config_file(filename, defaults=None):
            return "%s -- loaded" % filename

        mock_from_config_file.side_effect = stubbed_from_config_file
        dir = resource_filename(__name__, 'test_dashboard_data/dashboards/')
        dashboards = Dashboard.dashboards_from_dir(dir, None)

        expected = ["%s%s -- loaded" % (dir, file) for file in
                    ('dashboard1.yml', 'dashboard2.yml')]
        self.assertEqual(dashboards, expected)

    @patch.object(utils, 'slugify')
    @patch.object(utils, 'parse_interval')
    @patch.object(ToyWidget, 'from_config')
    def test_from_config(self, mock_widget_from_config, mock_parse_interval,
                         mock_slugify):
        """
        Should create a dashboard from a config dict.
        """
        def stubbed_widget_from_config(config, defaults):
            return "%s -- loaded" % config['name']

        mock_widget_from_config.side_effect = stubbed_widget_from_config
        mock_slugify.return_value = 'test-dashboard'
        mock_parse_interval.return_value = 2

        dashboard = StubbedDashboard.from_config({
            'name': 'test dashboard',
            'title': 'Test Dashboard',
            'request_interval': '2s',
            'share_id': 'this-is-a-share-id',
            'widgets': [
                'layoutfn1',
                {
                    'name': 'widget1',
                    'type': 'diamondash.tests.test_dashboard.ToyWidget',
                },
                'layoutfn2',
                {
                    'name': 'widget2',
                    'type': 'diamondash.tests.test_dashboard.ToyWidget',
                },
            ]
        })

        mock_slugify.assert_called_with('test dashboard')
        self.assertEqual(dashboard.name, 'test-dashboard')
        self.assertEqual(dashboard.title, 'Test Dashboard')
        self.assertEqual(dashboard.client_config['requestInterval'], 2000)
        self.assertEqual(dashboard.client_config['name'], 'test-dashboard')
        self.assertEqual(dashboard.share_id, 'this-is-a-share-id')
        self.assertEqual(dashboard.widgets, [
            'layoutfn1',
            'widget1 -- loaded',
            'layoutfn2',
            'widget2 -- loaded',
        ])

    def test_from_config_for_no_name(self):
        """
        Should raise an exception when given a dashboard config without a name
        key.
        """
        self.assertRaises(ConfigError, Dashboard.from_config, {})

    def test_from_config_for_no_title(self):
        """
        Should create a dashboard with a title set to the name passed into
        the config if no title is in the config.
        """
        dashboard = StubbedDashboard.from_config({
            'name': 'Test Dashboard',
            'widgets': []
        })
        self.assertEqual(dashboard.title, 'Test Dashboard')

    def test_from_config_for_no_widgets(self):
        """
        Should raise an exception when given a dashboard config without a
        widgets key.
        """
        self.assertRaises(ConfigError, Dashboard.from_config, {})
