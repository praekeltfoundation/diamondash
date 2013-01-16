from twisted.trial import unittest

from diamondash.utils import slugify
from diamondash.widgets.widget import Widget
from diamondash.exceptions import ConfigError

from diamondash.tests.utils import restore_from_stub, stub_classmethod


class ToyWidget(Widget):
    MAX_COLUMN_SPAN = 4
    MODEL = ('toy/toy-widget', 'ToyWidgetModel')
    VIEW = ('toy/toy-widget', 'ToyWidgetView')


class WidgetTestCase(unittest.TestCase):
    def test_parse_width(self):
        """
        Should clamp the passed in width value between 1 and the maximum
        widget column span.
        """
        self.assertEqual(ToyWidget.parse_width(0), 1)
        self.assertEqual(ToyWidget.parse_width(1), 1)
        self.assertEqual(ToyWidget.parse_width(5), 4)
        self.assertEqual(ToyWidget.parse_width(3), 3)
        self.assertEqual(ToyWidget.parse_width(4), 4)

    def test_parse_config(self):
        """
        Should parse the config, altering it accordignly to configure the
        widget.
        """
        def stubbed_parse_width(cls, width):
            return '%s -- parsed' % str(width)

        stub_classmethod(ToyWidget, 'parse_width', stubbed_parse_width)
        config = ToyWidget.parse_config({
            'name': 'Test Widget',
            'title': 'Test Widget',
            'width': 2
        })

        self.assertEqual(config, {
            'name': slugify('Test Widget'),
            'title': 'Test Widget',
            'width': '2 -- parsed',
            'client_config':  {
                'name': slugify('Test Widget'),
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
        config = ToyWidget.parse_config({'name': 'Test Widget'})
        self.assertEqual(config['title'], 'Test Widget')

    def test_parse_config_for_no_width(self):
        """
        Should set the widget width to a value of 1 if no width value is given.
        """
        def stubbed_parse_width(cls, width):
            return None

        stub_classmethod(ToyWidget, 'parse_width', stubbed_parse_width)
        config = ToyWidget.parse_config({
            'name': 'Test Widget',
            'title': 'Test Widget'
        })

        self.assertEqual(config['width'], 1)
        restore_from_stub(stubbed_parse_width)
