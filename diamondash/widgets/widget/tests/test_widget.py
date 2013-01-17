from twisted.trial import unittest

from diamondash import utils
from diamondash.widgets.widget import Widget
from diamondash.exceptions import ConfigError

from diamondash.tests.utils import (
    stub_fn, stub_classmethod, restore_from_stub)


class ToyWidget(Widget):
    MIN_COLUMN_SPAN = 4
    MAX_COLUMN_SPAN = 8
    MODEL = ('toy/toy-widget', 'ToyWidgetModel')
    VIEW = ('toy/toy-widget', 'ToyWidgetView')


class WidgetTestCase(unittest.TestCase):
    def test_parse_config(self):
        """
        Should parse the config, altering it accordignly to configure the
        widget.
        """
        def stubbed_insert_defaults_by_key(key, original, defaults):
            original.update({'defaults_inserted': True})
            return original

        def stubbed_parse_width(cls, width):
            return '%s -- parsed' % str(width)

        stub_classmethod(ToyWidget, 'parse_width', stubbed_parse_width)
        stub_fn(utils, 'insert_defaults_by_key',
                stubbed_insert_defaults_by_key)

        config = ToyWidget.parse_config({
            'name': 'Test Widget',
            'title': 'Test Widget',
            'width': 2
        })

        self.assertEqual(config, {
            'name': utils.slugify('Test Widget'),
            'title': 'Test Widget',
            'defaults_inserted': True,
            'width': '2 -- parsed',
            'client_config':  {
                'name': utils.slugify('Test Widget'),
                'model': {
                    'className': 'ToyWidgetModel',
                    'modulePath': 'widgets/toy/toy-widget',
                },
                'view': {
                    'className': 'ToyWidgetView',
                    'modulePath': 'widgets/toy/toy-widget',
                }
            }
        })

        restore_from_stub(stubbed_parse_width)
        restore_from_stub(stubbed_insert_defaults_by_key)

    def test_from_config_for_no_name(self):
        """
        Should raise an exception when given widget dashboard config without a
        name key.
        """
        self.assertRaises(ConfigError, Widget.parse_config, {})

    def test_parse_config_for_no_title(self):
        """
        Should set the widget title to the name passed into the config if no
        title is in the config.
        """
        def stubbed_insert_defaults_by_key(key, original, defaults):
            return original

        stub_fn(utils, 'insert_defaults_by_key',
                stubbed_insert_defaults_by_key)

        config = ToyWidget.parse_config({'name': 'Test Widget'})
        self.assertEqual(config['title'], 'Test Widget')

        restore_from_stub(stubbed_insert_defaults_by_key)

    def test_parse_config_for_no_width(self):
        """
        Should set the widget width to the minimum column span if no width
        value is given.
        """
        def stubbed_insert_defaults_by_key(key, original, defaults):
            return original

        def stubbed_parse_width(cls, width):
            return None

        stub_classmethod(ToyWidget, 'parse_width', stubbed_parse_width)
        stub_fn(utils, 'insert_defaults_by_key',
                stubbed_insert_defaults_by_key)

        config = ToyWidget.parse_config({
            'name': 'Test Widget',
            'title': 'Test Widget'
        })

        self.assertEqual(config['width'], ToyWidget.MIN_COLUMN_SPAN)

        restore_from_stub(stubbed_insert_defaults_by_key)
        restore_from_stub(stubbed_parse_width)

    def test_parse_width(self):
        """
        Should clamp the passed in width value between 1 and the maximum
        widget column span.
        """
        self.assertEqual(ToyWidget.parse_width(0), 4)
        self.assertEqual(ToyWidget.parse_width(5), 5)
        self.assertEqual(ToyWidget.parse_width(9), 8)
        self.assertEqual(ToyWidget.parse_width(8), 8)
        self.assertEqual(ToyWidget.parse_width(4), 4)
