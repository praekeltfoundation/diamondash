"""Tests for diamondash's dashboard"""

from twisted.trial import unittest
from twisted.web.template import flattenString

from diamondash import utils
from diamondash.config import ConfigError
from diamondash.widgets.widget import WidgetConfig
from diamondash.widgets.dynamic import DynamicWidgetConfig
from diamondash.dashboard import (
    DashboardRowConfig, DashboardRowConfigs, DashboardWidgetConfigs,
    DashboardConfig, Dashboard, DashboardPage)


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
            'new_row',
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
    config = DashboardConfig(mk_config_data(**overrides))
    return Dashboard(config)


class DashboardRowConfigTestCase(unittest.TestCase):
    def test_widget_acceptance(self):
        row = DashboardRowConfig()

        self.assertTrue(row.accepts_widget(WidgetConfig({
            'name': 'widget1',
            'width': 3
        })))

        row.add_widget(WidgetConfig({
            'name': 'widget2',
            'width': 8
        }))

        self.assertFalse(row.accepts_widget(WidgetConfig({
            'name': 'widget3',
            'width': 6
        })))

    def test_widget_adding(self):
        row = DashboardRowConfig()

        row.add_widget(WidgetConfig({
            'name': 'widget1',
            'width': 3
        }))

        row.add_widget(WidgetConfig({
            'name': 'widget2',
            'width': 4
        }))

        self.assertEqual(row.remaining_width, 5)
        self.assertEqual(row, {
            'widgets': [
                {'name': 'widget1'},
                {'name': 'widget2'}]
        })


class DashboardRowConfigsTestCase(unittest.TestCase):
    def test_row_creation(self):
        rows = DashboardRowConfigs()

        rows.add_widget(WidgetConfig({
            'name': 'widget1',
            'width': 3
        }))

        rows.new_row()

        rows.add_widget(WidgetConfig({
            'name': 'widget2',
            'width': 3
        }))

        self.assertEqual(rows.to_list(), [{
            'widgets': [
                {'name': 'widget1'}]
        }, {
            'widgets': [
                {'name': 'widget2'}]
        }])

    def test_widget_adding(self):
        rows = DashboardRowConfigs()

        rows.add_widget(WidgetConfig({
            'name': 'widget1',
            'width': 3
        }))

        rows.add_widget(WidgetConfig({
            'name': 'widget2',
            'width': 8
        }))

        rows.add_widget(WidgetConfig({
            'name': 'widget3',
            'width': 3
        }))

        rows.add_widget(WidgetConfig({
            'name': 'widget4',
            'width': 4
        }))

        self.assertEqual(rows.to_list(), [{
            'widgets': [
                {'name': 'widget1'},
                {'name': 'widget2'}]
        }, {
            'widgets': [
                {'name': 'widget3'},
                {'name': 'widget4'}]
        }])


class DashboardWidgetConfigsTestCase(unittest.TestCase):
    def test_row_fitting(self):
        widgets = DashboardWidgetConfigs()

        widgets.add_widget(WidgetConfig({
            'width': 3,
            'name': 'widget1',
            'type': 'diamondash.widgets.widget.Widget',
        }))

        widgets.add_widget(WidgetConfig({
            'width': 8,
            'name': 'widget2',
            'type': 'diamondash.widgets.widget.Widget',
        }))

        widgets.add_widget(WidgetConfig({
            'width': 3,
            'name': 'widget3',
            'type': 'diamondash.widgets.widget.Widget',
        }))

        widgets.add_widget(WidgetConfig({
            'width': 4,
            'name': 'widget4',
            'type': 'diamondash.widgets.widget.Widget',
        }))

    def test_widget_parsing_for_dynamic_widgets(self):
        widgets = DashboardWidgetConfigs({
            'type': 'diamondash.tests.utils.ToyBackend',
            'url': 'http://127.0.0.1:3000',
        })

        config = widgets.parse_widget({
            'name': 'widget2',
            'type': 'diamondash.tests.utils.ToyDynamicWidget',
        })

        self.assertTrue(isinstance(config, DynamicWidgetConfig))
        self.assertTrue(config['name'], 'widget2')
        self.assertEqual(config['backend'], {
            'type': 'diamondash.tests.utils.ToyBackend',
            'url': 'http://127.0.0.1:3000',
            'metrics': [],
        })

    def test_widget_parsing_for_static_widgets(self):
        widgets = DashboardWidgetConfigs({
            'type': 'diamondash.tests.utils.ToyBackend',
            'url': 'http://127.0.0.1:3000',
        })

        config = widgets.parse_widget({
            'name': 'widget1',
            'type': 'diamondash.widgets.widget.Widget',
        })

        self.assertTrue(isinstance(config, WidgetConfig))
        self.assertTrue(config['name'], 'widget1')
        self.assertTrue('backend' not in config)


class DashboardConfigTestCase(unittest.TestCase):
    def test_parsing(self):
        """
        Should create a dashboard from a config dict.
        """
        config = DashboardConfig(mk_config_data())

        self.assertEqual(config['name'], 'some-dashboard')
        self.assertEqual(config['title'], 'Some Dashboard')

        w1_config, w2_config = config['widgets']
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

        self.assertEqual(config['rows'], [
            {'widgets': [{'name': 'widget1'}]},
            {'widgets': [{'name': 'widget2'}]}
        ])

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
        return WidgetConfig(utils.add_dicts({
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
