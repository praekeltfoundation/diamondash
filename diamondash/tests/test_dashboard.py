"""Tests for diamondash's dashboard"""

from twisted.trial import unittest
from twisted.web.template import flattenString

from diamondash import utils
from diamondash.config import ConfigError
from diamondash.dashboard import DashboardConfig, Dashboard, DashboardPage
from diamondash.widgets.widget import WidgetConfig
from diamondash.widgets.dynamic import DynamicWidgetConfig


def mk_config_data(**overrides):
    return utils.add_dicts({
        'name': 'Some Dashboard',
        'poll_interval': '2s',
        'share_id': 'some-dashboard-share-id',
        'widgets': [
            {
                'name': 'widget1',
                'type': 'diamondash.widgets.widget.Widget',
            },
            'newrow',
            {
                'name': 'widget2',
                'type': 'diamondash.tests.utils.ToyDynamicWidget',
            }
        ],
        'backend': {
            'type': 'diamondash.tests.utils.ToyBackend',
            'url': 'http://127.0.0.1:3000',
        }
    }, overrides)


def mk_dashboard(**overrides):
    config = DashboardConfig.from_dict(mk_config_data(**overrides))
    return Dashboard(config)


class DashboardConfigTestCase(unittest.TestCase):
    def test_parsing(self):
        """
        Should create a dashboard from a config dict.
        """
        config = DashboardConfig.from_dict(mk_config_data())

        self.assertEqual(config['name'], 'some-dashboard')
        self.assertEqual(config['title'], 'Some Dashboard')

        w1_config, newrow, w2_config = config['widgets']
        self.assertTrue(isinstance(w1_config, WidgetConfig))
        self.assertTrue(w1_config['name'], 'widget1')
        self.assertTrue('backend' not in w1_config)

        self.assertTrue(isinstance(w2_config, DynamicWidgetConfig))
        self.assertTrue(w2_config['name'], 'widget2')
        self.assertEqual(w2_config['backend'], {
            'type': 'diamondash.tests.utils.ToyBackend',
            'url': 'http://127.0.0.1:3000',
            'metrics': [],
        })

        self.assertEqual(newrow, 'newrow')

    def test_parsing_for_no_name(self):
        """
        Should raise an exception when given a dashboard config without a name
        key.
        """
        self.assertRaises(ConfigError, DashboardConfig.parse, {})

    def test_parse_config_for_no_widgets(self):
        """
        Should raise an exception when given a dashboard config without a
        widgets key.
        """
        config = mk_config_data()
        del config['widgets']
        self.assertRaises(ConfigError, DashboardConfig.parse, config)


class DashboardTestCase(unittest.TestCase):
    def mk_widget_config(self, **overrides):
        return WidgetConfig.from_dict(utils.add_dicts({
            'type': 'diamondash.widgets.widget.Widget',
            'name': 'toy',
            'title': 'Toy',
            'width': 2
        }, overrides))

    def test_widget_adding(self):
        """Should add a widget to the dashboard."""
        dashboard = mk_dashboard()
        widget_config = self.mk_widget_config()
        dashboard.add_widget(widget_config)

        self.assertEqual(
            dashboard.widgets_by_name['toy'].config,
            widget_config)

        self.assertEqual(
            dashboard.widgets[-1].config,
            widget_config)

        self.assertEqual(
            dashboard.last_row.widgets[-1].widget.config,
            widget_config)

        self.assertEqual(dashboard.last_row.width, 6)

    def test_row_building(self):
        """
        Should add a new row if there is no space for the widget being added on
        the current row.
        """
        dashboard = mk_dashboard(widgets=[])

        dashboard.add_widget(self.mk_widget_config(width=8))
        self.assertEqual(len(dashboard.rows), 1)
        self.assertEqual(dashboard.last_row.width, 8)

        dashboard.add_widget(self.mk_widget_config(width=4))
        self.assertEqual(len(dashboard.rows), 1)
        self.assertEqual(dashboard.last_row.width, 12)

        dashboard.add_widget(self.mk_widget_config(width=4))
        self.assertEqual(len(dashboard.rows), 2)
        self.assertEqual(dashboard.last_row.width, 4)


class DashboardPageTestCase(unittest.TestCase):
    def test_brand_rendering_for_shared_pages(self):
        page = DashboardPage(mk_dashboard(), shared=True)
        d = flattenString(None, page)

        def assert_brand_rendering(response):
            self.assertTrue('<a href="#" class="brand">' in response)

        d.addCallback(assert_brand_rendering)
        return d

    def test_brand_rendering_for_non_shared_pages(self):
        page = DashboardPage(mk_dashboard(), shared=False)
        d = flattenString(None, page)

        def assert_brand_rendering(response):
            self.assertTrue('<a href="/" class="brand">' in response)

        d.addCallback(assert_brand_rendering)
        return d
