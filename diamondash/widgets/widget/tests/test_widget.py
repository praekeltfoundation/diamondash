from twisted.trial import unittest

from diamondash.widgets.widget import Widget
from diamondash import ConfigError


class ToyWidget(Widget):
    MIN_COLUMN_SPAN = 4
    MAX_COLUMN_SPAN = 8
    MODEL = 'ToyWidgetModel'
    VIEW = 'ToyWidgetView'


class WidgetTestCase(unittest.TestCase):
    def test_parse_config(self):
        """
        Should parse the config, altering it accordignly to configure the
        widget.
        """

        config = {
            'name': u'Test Widget',
            'title': 'Test Widget',
            'width': 2
        }
        class_defaults = {'SomeWidgetType': "some widget's defaults"}

        parsed_config = ToyWidget.parse_config(config, class_defaults)
        self.assertEqual(parsed_config, {
            'name': 'test-widget',
            'title': 'Test Widget',
            'width': 4,
            'client_config':  {
                'model': {'name': 'test-widget'},
                'view': {},
                'modelClass': 'ToyWidgetModel',
                'viewClass': 'ToyWidgetView',
            }
        })

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
        config = {'name': u'Test Widget'}
        parsed_config = ToyWidget.parse_config(config)
        self.assertEqual(parsed_config['title'], 'Test Widget')

    def test_parse_config_for_no_width(self):
        """
        Should set the widget width to the minimum column span if no width
        value is given.
        """
        config = {
            'name': u'Test Widget',
            'title': u'Test Widget'
        }
        parsed_config = ToyWidget.parse_config(config)
        self.assertEqual(parsed_config['width'], ToyWidget.MIN_COLUMN_SPAN)

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
