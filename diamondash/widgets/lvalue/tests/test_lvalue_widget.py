import json

from mock import patch
from twisted.trial import unittest

from diamondash import utils
from diamondash.widgets.lvalue import LValueWidget
from diamondash.widgets.graphite import GraphiteWidgetMetric
from diamondash.exceptions import ConfigError


class StubbedLValueWidget(LValueWidget):
    DEFAULTS = {'time_range': '3h'}

    def set_metric(self, metric):
        self.metric = metric


class LValueWidgetTestCase(unittest.TestCase):
    @staticmethod
    def mk_lvalue_widget(**kwargs):
        kwargs = utils.setdefaults(kwargs, {
            'name': 'some-widget',
            'title': 'Some Widget',
            'client_config': {},
            'width': 2,
            'from_time': 3600,
            'time_range': 3600,
            'bucket_size': 60,
            'graphite_url': 'some-url',
            'metric': None
        })
        return StubbedLValueWidget(**kwargs)

    @staticmethod
    def mk_graphite_widget_metric(**kwargs):
        kwargs = utils.setdefaults(kwargs, {
            'target': 'some.target',
            'wrapped_target': 'some.target -- wrapped',
            'null_filter': 'some-null-filter',
            'name': 'some-widget',
            'title': 'some widget',
            'client_config': {},
            'graphite_url': 'fake-graphite-url',
        })
        return GraphiteWidgetMetric(**kwargs)

    @patch.object(GraphiteWidgetMetric, 'from_config')
    def test_parse_config(self, mock_GraphiteWidgetMetric_from_config):
        """
        Should parse the config, altering it accordingly to configure the
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

        mock_GraphiteWidgetMetric_from_config.return_value = 'fake-metric'

        parsed_config = StubbedLValueWidget.parse_config(config, defaults)

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

    def test_handle_graphite_render_response(self):
        data = [
            {
                'target': 'some.target',
                'datapoints': [
                    [1346269.0, 1340875975],
                    [2178309.0, 1340875980],
                    [3524578.0, 1340875985],
                    [5702887.0, 1340875990],
                    [9227465.0, 1340875995]]
            }
        ]

        widget = self.mk_lvalue_widget(
            time_range=3600,
            metric=self.mk_graphite_widget_metric(target='some.target'))

        results = widget.handle_graphite_render_response(data)
        self.assertEqual(results, json.dumps({
            'lvalue': 9227465.0,
            'from': 1340875995,
            'to': 1340875995 + 3600 - 1,
            'diff': 9227465.0 - 5702887.0,
            'percentage': 0.61803398874990854,
        }))
