from mock import patch
from twisted.trial import unittest

from diamondash import utils
from diamondash.widgets.widget import Widget
from diamondash.exceptions import ConfigError


class ToyWidget(Widget):
    MIN_COLUMN_SPAN = 4
    MAX_COLUMN_SPAN = 8
    MODEL = ('toy/toy-widget', 'ToyWidgetModel')
    VIEW = ('toy/toy-widget', 'ToyWidgetView')


class WidgetTestCase(unittest.TestCase):
    @patch.object(utils, 'slugify')
    @patch.object(ToyWidget, 'parse_width')
    @patch.object(utils, 'insert_defaults_by_key')
    def test_parse_config(self, mock_insert_defaults_by_key, mock_parse_width,
                          mock_slugify):
        """
        Should parse the config, altering it accordignly to configure the
        widget.
        """

        config = {
            'name': 'Test Widget',
            'title': 'Test Widget',
            'width': 2
        }
        defaults = {'SomeWidgetType': "some widget's defaults"}

        mock_parse_width.return_value = 4
        mock_slugify.return_value = 'test-widget'
        mock_insert_defaults_by_key.side_effect = (
            lambda key, original, defaults: original)

        parsed_config = ToyWidget.parse_config(config, defaults)
        self.assertEqual(parsed_config, {
            'name': 'test-widget',
            'title': 'Test Widget',
            'width': 4,
            'client_config':  {
                'name': 'test-widget',
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
        self.assertTrue(mock_insert_defaults_by_key.called)
        mock_slugify.assert_called_with('Test Widget')
        mock_parse_width.assert_called_with(2)

    def test_from_config_for_no_name(self):
        """
        Should raise an exception when given widget dashboard config without a
        name key.
        """
        self.assertRaises(ConfigError, Widget.parse_config, {})

    @patch.object(utils, 'insert_defaults_by_key')
    def test_parse_config_for_no_title(self, mock_insert_defaults_by_key):
        """
        Should set the widget title to the name passed into the config if no
        title is in the config.
        """
        config = {'name': 'Test Widget'}
        mock_insert_defaults_by_key.return_value = config
        parsed_config = ToyWidget.parse_config(config)
        self.assertEqual(parsed_config['title'], 'Test Widget')

    @patch.object(utils, 'insert_defaults_by_key')
    def test_parse_config_for_no_width(self, mock_insert_defaults_by_key):
        """
        Should set the widget width to the minimum column span if no width
        value is given.
        """
        config = {
            'name': 'Test Widget',
            'title': 'Test Widget'
        }
        mock_insert_defaults_by_key.return_value = config
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
