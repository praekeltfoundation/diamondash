from mock import patch
from twisted.trial import unittest

from diamondash import utils
from diamondash.widgets.lvalue import LValueWidget
from diamondash.exceptions import ConfigError


class LValueWidgetTestCase(unittest.TestCase):

    @patch.object(utils, 'insert_defaults_by_key')
    @patch.object(utils, 'parse_interval')
    @patch.object(LValueWidget, 'format_metric_target')
    @patch.object(LValueWidget, 'build_request_url')
    @patch.object(LValueWidget, 'DEFAULTS')
    def test_parse_config(self, mock_lvalue_defaults, mock_build_request_url,
                          mock_format_metric_target, mock_parse_interval,
                          mock_insert_defaults_by_key):
        """
        Should parse the config, altering it accordignly to configure the
        widget.
        """
        def stubbed_format_metric_target(cls, target, bucket_size):
            return target, bucket_size

        def stubbed_build_request_url(cls, graphite_url, targets, from_param):
            return graphite_url, targets, from_param

        config = {
            'name': 'test-lvalue-widget',
            'graphite_url': 'fake_graphite_url',
            'metric': 'vumi.random.count.sum',
            'time_range': '1h',
        }
        defaults = {'SomeWidgetType': "some widget's defaults"}

        mock_lvalue_defaults.side_effect = {'time_range': '5h'}
        mock_insert_defaults_by_key.return_value = config
        mock_parse_interval.return_value = 3600
        mock_format_metric_target.return_value = (
            'fake_formatted_metric_target')
        mock_build_request_url.return_value = 'fake_request_url'

        parsed_config = LValueWidget.parse_config(config, defaults)
        mock_insert_defaults_by_key.assert_called_with(
            'diamondash.widgets.lvalue.lvalue_widget', config, defaults)
        mock_format_metric_target.assert_called_with(
            'vumi.random.count.sum', 3600)
        mock_build_request_url.assert_called_with(
            'fake_graphite_url', ['fake_formatted_metric_target'], 7200)
        self.assertEqual(parsed_config['request_url'], 'fake_request_url')

    def test_parse_config_for_no_metric(self):
        """
        Should raise an exception if the lvalue config has no `metric` key
        """
        config = {
            'name': 'test-lvalue-widget',
            'graphite_url': 'fake_graphite_url',
        }
        self.assertRaises(ConfigError, LValueWidget.parse_config, config)
