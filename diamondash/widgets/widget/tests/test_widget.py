from twisted.trial import unittest

from diamondash.widgets.widget import WidgetConfig
from diamondash.config import ConfigError


class WidgetConfigTestCase(unittest.TestCase):
    def test_parsing(self):
        config = WidgetConfig({
            'name': u'Test Widget',
            'title': 'Test Widget',
            'width': 4
        })

        self.assertEqual(config['name'], 'test-widget')
        self.assertEqual(config['title'], 'Test Widget')
        self.assertEqual(config['width'], 4)

    def test_parsing_for_no_name(self):
        """
        Should raise an exception when given widget dashboard config without a
        name key.
        """
        self.assertRaises(ConfigError, WidgetConfig, {})

    def test_parsing_for_no_title(self):
        """
        Should set the widget title to the name passed into the config if no
        title is in the config.
        """
        config = {'name': u'Test Widget'}
        parsed_config = WidgetConfig(config)
        self.assertEqual(parsed_config['title'], 'Test Widget')

    def test_parsing_for_no_width(self):
        """
        Should set the widget width to the minimum column span if no width
        value is given.
        """
        config = WidgetConfig({
            'name': u'Test Widget',
            'title': u'Test Widget'
        })
        self.assertEqual(config['width'], 3)

    def test_parse_width(self):
        """
        Should clamp the passed in width value between 1 and the maximum
        widget column span.
        """
        self.assertEqual(WidgetConfig.parse_width(0), 3)
        self.assertEqual(WidgetConfig.parse_width(3), 3)
        self.assertEqual(WidgetConfig.parse_width(4), 4)
        self.assertEqual(WidgetConfig.parse_width(11), 11)
        self.assertEqual(WidgetConfig.parse_width(12), 12)
        self.assertEqual(WidgetConfig.parse_width(13), 12)
