import json

from mock import Mock, patch, call
from twisted.trial import unittest

from diamondash import utils
from diamondash.widgets.lvalue import LValueWidget
from diamondash.widgets.graphite import (
    GraphiteWidgetMetric, SingleMetricGraphiteWidget)
from diamondash.exceptions import ConfigError


class StubbedLValueWidget(LValueWidget):
    DEFAULTS = {'time_range': '3h'}

    def __init__(self, target=None, time_range=None):
        self.target = target
        self.time_range = time_range


class LValueWidgetTestCase(unittest.TestCase):

    @patch.object(utils, 'set_key_defaults')
    @patch.object(utils, 'parse_interval')
    @patch.object(GraphiteWidgetMetric, 'from_config')
    def test_parse_config(self, mock_GraphiteWidgetMetric_from_config,
                          mock_parse_interval, mock_set_key_defaults):
        """
        Should parse the config, altering it accordignly to configure the
        widget.
        """
        config = {
            'name': 'test-lvalue-widget',
            'graphite_url': 'fake_graphite_url',
            'target': 'vumi.random.count.sum',
            'time_range': '1h',
            'metric_defaults': {'null_filter': 'zeroize'}
        }
        defaults = {'SomeWidgetType': "some widget's defaults"}

        mock_parse_interval.return_value = 3600
        mock_GraphiteWidgetMetric_from_config.return_value = 'fake-metric'
        mock_set_key_defaults.side_effect = lambda k, original, d: original

        parsed_config = StubbedLValueWidget.parse_config(config, defaults)
        mock_set_key_defaults.assert_called()
        mock_parse_interval.assert_called_with('1h')

        mock_GraphiteWidgetMetric_from_config.assert_called_with(
            {'target': config['target'], 'bucket_size': 3600},
            {'null_filter': 'zeroize'})

        self.assertEqual(parsed_config['time_range'], 3600)
        self.assertEqual(parsed_config['bucket_size'], 3600)
        self.assertEqual(parsed_config['from_time'], 7200)
        self.assertEqual(parsed_config['metric'], 'fake-metric')

    def test_parse_config_for_no_metric(self):
        """
        Should raise an exception if the lvalue config has no `metric` key
        """
        config = {
            'name': 'test-lvalue-widget',
            'graphite_url': 'fake_graphite_url',
        }
        self.assertRaises(ConfigError, LValueWidget.parse_config, config)

    @patch.object(utils, 'format_time')
    @patch.object(utils, 'format_number')
    def test_build_render_response(self, mock_format_number, mock_format_time):
        widget = StubbedLValueWidget(target='some.target', time_range=3600)
        datapoints = [
            [1346269.0, 1340875975],
            [2178309.0, 1340875980],
            [3524578.0, 1340875985],
            [5702887.0, 1340875990],
            [9227465.0, 1340875995]]

        mock_format_time.side_effect = ["2012-06-28 09:33", "2012-06-28 10:33"]
        mock_format_number.side_effect = ["9.227M", "3.525M"]

        results = widget.build_render_response(datapoints)

        self.assertEqual(
            mock_format_time.call_args_list,
            [call(1340875995), call(1340875995 + 3600 - 1)])

        self.assertEqual(
            mock_format_number.call_args_list,
            [call(9227465.0), call(9227465.0 - 5702887.0)])

        expected_results = json.dumps({
            'lvalue': "9.227M",
            'from': "2012-06-28 09:33",
            'to': "2012-06-28 10:33",
            'diff': "+3.525M",
            'percentage': "62%",
        })
        self.assertEqual(results, expected_results)

    @patch.object(
        SingleMetricGraphiteWidget, 'handle_graphite_render_response')
    def test_handle_graphite_render_response(self, mock_overriden_method):

        mock_overriden_method.return_value = ('processed-datapoints')
        widget = StubbedLValueWidget()
        widget.build_render_response = Mock(
            return_value='built-render-response')

        result = widget.handle_graphite_render_response('response-data')
        mock_overriden_method.assert_called_with('response-data')
        widget.build_render_response.assert_called_with('processed-datapoints')
        self.assertEqual(result, 'built-render-response')
