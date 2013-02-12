"""Tests for diamondash's dashboard"""

from mock import Mock
from twisted.trial import unittest

from diamondash.dashboard import Dashboard, WidgetRow
from diamondash.widgets.widget import Widget
from diamondash import utils, ConfigError


class StubbedDashboard(Dashboard):
    LAYOUT_FUNCTIONS = {
        'layoutfn1': lambda x: x,
        'layoutfn2': lambda x: x
    }


class ToyWidget(Widget):
    __DEFAULTS = {'some-option': 'some-value'}
    __CONFIG_TAG = 'diamondash.tests.test_dashboard.ToyWidget'

    @classmethod
    def from_config(cls, config, class_defaults):
        return "%s -- created" % config['name']


class DashboardTestCase(unittest.TestCase):
    def mk_dashboard(self, **kwargs):
        kwargs = utils.update_dict(kwargs, {
            'name': 'some-dashboard',
            'title': 'Some Dashboard',
            'widgets': [],
            'client_config': {},
        })

        return Dashboard(**kwargs)

    def test_new_row(self):
        """
        Should append an empty row and set the last row width to 0.
        """
        dashboard = self.mk_dashboard()
        existing_row = dashboard.last_row
        dashboard._new_row()
        self.assertEqual(dashboard.rows, [existing_row, dashboard.last_row])
        self.assertNotEqual(dashboard.last_row, existing_row)

    def test_add_widget(self):
        """Should add a widget to the dashboard."""

        dashboard = self.mk_dashboard()
        widget = ToyWidget(
            name='toy',
            title='Toy',
            client_config='toy_client_config',
            width=2)
        dashboard.add_widget(widget)

        self.assertEqual(dashboard.widgets_by_name['toy'], widget)
        self.assertEqual(dashboard.widgets[0], widget)
        self.assertEqual(dashboard.rows[0].widgets[0].widget, widget)
        self.assertEqual(dashboard.last_row.width, 2)
        self.assertEqual(dashboard.client_config['widgets'][0],
                         'toy_client_config')

    def test_add_widget_for_layout_fn(self):
        """
        Should call the appropriate layout function if the function's name is
        passed in as a 'widget'.
        """
        dashboard = self.mk_dashboard()
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
        dashboard = self.mk_dashboard()
        dashboard.last_row = WidgetRow()
        dashboard.last_row.width = 3

        widget = ToyWidget(name='toy', title='Toy', width=2,
                           client_config='toy_client_config')
        self.patch(Dashboard, 'MAX_WIDTH', 4)

        dashboard.add_widget(widget)
        self.assertEqual(dashboard.last_row.width, 2)

    def test_parse_config(self):
        """
        Should create a dashboard from a config dict.
        """
        config = StubbedDashboard.parse_config({
            'name': u'some dashboard',
            'title': 'Some Dashboard',
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

        self.assertEqual(config['name'], 'some-dashboard')
        self.assertEqual(config['title'], 'Some Dashboard')
        self.assertEqual(config['client_config'], {
            'name': 'some-dashboard',
            'requestInterval': 2000
        })
        self.assertEqual(config['share_id'], 'this-is-a-share-id')
        self.assertEqual(config['widgets'], [
            'layoutfn1',
            'widget1 -- created',
            'layoutfn2',
            'widget2 -- created',
        ])

    def test_parse_config_for_defaults(self):
        class_defaults = {
            Dashboard._Dashboard__CONFIG_TAG: {
                'some-field': 'lerp',
                'some-other-field': 23,
            }
        }
        config = StubbedDashboard.parse_config({
            'name': u'Test Dashboard',
            'widgets': [],
            'defaults': {
                Dashboard._Dashboard__CONFIG_TAG: {'some-field': 'larp'}
            }
        }, class_defaults)
        self.assertEqual(config['title'], 'Test Dashboard')
        self.assertFalse(config.get('defaults'))
        self.assertEqual(config['some-field'], 'larp')
        self.assertEqual(config['some-other-field'], 23)

    def test_parse_config_for_no_name(self):
        """
        Should raise an exception when given a dashboard config without a name
        key.
        """
        self.assertRaises(ConfigError, Dashboard.parse_config, {})

    def test_parse_config_for_no_title(self):
        """
        Should create a dashboard with a title set to the name passed into
        the config if no title is in the config.
        """
        config = StubbedDashboard.parse_config({
            'name': u'Test Dashboard',
            'widgets': []
        })
        self.assertEqual(config['title'], 'Test Dashboard')

    def test_parse_config_for_no_widgets(self):
        """
        Should raise an exception when given a dashboard config without a
        widgets key.
        """
        self.assertRaises(ConfigError, Dashboard.parse_config, {})
