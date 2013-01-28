"""Tests for diamondash's dashboard"""

from mock import Mock
from twisted.trial import unittest

from diamondash.dashboard import Dashboard, WidgetRow
from diamondash.widgets.widget import Widget
from diamondash.exceptions import ConfigError


class StubbedDashboard(Dashboard):
    LAYOUT_FUNCTIONS = {
        'layoutfn1': lambda x: x,
        'layoutfn2': lambda x: x
    }

    def add_widget(self, widget):
        self.widgets.append(widget)


class ToyWidget(Widget):
    STYLESHEETS = ('toy/style.css',)
    JAVASCRIPTS = ('toy/toy-widget',)

    @classmethod
    def from_config(cls, config, defaults):
        return "%s -- loaded" % config['name']


class DashboardTestCase(unittest.TestCase):
    def test_new_row(self):
        """
        Should append an empty row and set the last row width to 0.
        """
        dashboard = Dashboard('test-dashboard', 'test dashboard', [], {})
        existing_row = dashboard.last_row
        dashboard._new_row()
        self.assertEqual(dashboard.rows, [existing_row, dashboard.last_row])
        self.assertNotEqual(dashboard.last_row, existing_row)

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
        self.assertEqual(dashboard.rows[0].widgets[0].widget, widget)
        self.assertEqual(dashboard.last_row.width, 2)
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
        dashboard = Dashboard('test-dashboard', 'Test Dashboard', [], {})

        mock_layoutfn = Mock()
        dashboard.LAYOUT_FUNCTIONS = {'mock': 'mock_layoutfn'}
        dashboard.mock_layoutfn = mock_layoutfn

        dashboard.add_widget('mock')
        self.assertTrue(mock_layoutfn.called)

    def test_add_widget_for_new_row(self):
        """
        Should add a new row if there is no space for the widget being added on
        the current row.
        """
        dashboard = Dashboard('test-dashboard', 'Test Dashboard', [], {})
        dashboard.last_row = WidgetRow()
        dashboard.last_row.width = 3

        widget = ToyWidget(name='toy', title='Toy', width=2,
                           client_config='toy_client_config')
        self.patch(Dashboard, 'MAX_WIDTH', 4)

        dashboard.add_widget(widget)
        self.assertEqual(dashboard.last_row.width, 2)

    def test_from_config(self):
        """
        Should create a dashboard from a config dict.
        """
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
