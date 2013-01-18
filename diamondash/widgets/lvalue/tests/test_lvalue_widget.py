import json

from mock import Mock, patch, call
from twisted.trial import unittest

from diamondash import utils
from diamondash.widgets.lvalue import LValueWidget
from diamondash.exceptions import ConfigError


class StubbedLValueWidget(LValueWidget):
    def __init__(self, target=None, time_range=None):
        self.target = target
        self.time_range = time_range


class LValueWidgetTestCase(unittest.TestCase):

    @patch.object(utils, 'insert_defaults_by_key')
    @patch.object(utils, 'parse_interval')
    @patch.object(LValueWidget, 'format_metric_target')
    @patch.object(LValueWidget, 'build_request_url')
    def test_parse_config(self, mock_build_request_url,
                          mock_format_metric_target, mock_parse_interval,
                          mock_insert_defaults_by_key):
        """
        Should parse the config, altering it accordignly to configure the
        widget.
        """
        config = {
            'name': 'test-lvalue-widget',
            'graphite_url': 'fake_graphite_url',
            'target': 'vumi.random.count.sum',
            'time_range': '1h',
        }
        defaults = {'SomeWidgetType': "some widget's defaults"}

        mock_insert_defaults_by_key.side_effect = (
            lambda key, original, defaults: original)
        mock_parse_interval.return_value = 3600
        mock_format_metric_target.return_value = (
            'fake_formatted_metric_target')
        mock_build_request_url.return_value = 'fake_request_url'

        parsed_config = LValueWidget.parse_config(config, defaults)
        self.assertTrue(mock_insert_defaults_by_key.called)
        mock_parse_interval.assert_called_with('1h')
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

    @patch.object(utils, 'find_dict_by_item')
    def test_handle_graphite_render_response(self, mock_find_dict_by_item):
        widget = StubbedLValueWidget(target='some.target', time_range=3600)

        data = [
            {
                'target': 'some.target',
                'datapoints': [[0, 1], [1, 2], [2, 3]]
            }, {
                'target': 'some.other.target',
                'datapoints': [[0, 2], [1, 4], [3, 6]]
            }
        ]

        mock_find_dict_by_item.return_value = {
            'target': 'some.target',
            'datapoints': [[0, 1], [1, 2], [2, 3]]
        }

        widget.build_render_response = Mock(return_value='fake_render_results')
        result = widget.handle_graphite_render_response(data)
        mock_find_dict_by_item.assert_called_with(
            data, 'target', 'some.target')
        widget.build_render_response.assert_called_with(
            [[0, 1], [1, 2], [2, 3]])
        self.assertEqual(result, 'fake_render_results')
