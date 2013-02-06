import json
from mock import patch
from twisted.trial import unittest

from diamondash import utils
from diamondash import ConfigError
from diamondash.widgets.graph import GraphWidget
from diamondash.backends.graphite import GraphiteBackend, GraphiteMetric


class GraphWidgetTestCase(unittest.TestCase):
    @staticmethod
    def mk_graph_widget(**kwargs):
        kwargs = utils.setdefaults(kwargs, {
            'name': 'some-widget',
            'title': 'Some Widget',
            'client_config': {},
            'width': 2,
            'from_time': 3600,
            'backend': None
        })
        return GraphWidget(**kwargs)

    @patch.object(GraphiteBackend, 'from_config')
    def test_parse_config(self, mock_GraphiteBackend_from_config):
        config = {
            'name': u'test-graph-widget',
            'graphite_url': 'fake_graphite_url',
            'metrics': [
                {'name': u'random sum', 'target':'vumi.random.count.sum'},
                {'name': u'random avg', 'target':'vumi.random.timer.avg'}],
            'time_range': '1d',
            'bucket_size': '1h',
            'metric_defaults': {
                'some_metric_config_option': 'some-metric-config-option'
            }
        }
        class_defaults = {'SomeWidgetType': "some widget's defaults"}
        mock_GraphiteBackend_from_config.return_value = 'fake-backend'

        parsed_config = GraphWidget.parse_config(config, class_defaults)
        mock_GraphiteBackend_from_config.assert_called_width({
            'from_time': '1d',
            'metrics': [
                {
                    'target':'vumi.random.count.sum',
                    'bucket_size': '1h',
                    'metadata': {
                        'name': 'random-sum',
                        'title': 'random sum',
                        'client_config': {
                            'name': 'random-sum',
                            'title': 'random sum',
                        },
                    },
                },
                {
                    'target':'vumi.random.timer.avg',
                    'bucket_size': '1h',
                    'metadata': {
                        'name': 'random-avg',
                        'title': 'random avg',
                        'client_config': {
                            'name': 'random-avg',
                            'title': 'random avg',
                        },
                    },
                },
            ]
        }, class_defaults)
        self.assertEqual(parsed_config['backend'], 'fake-backend')
        self.assertEqual(
            parsed_config['client_config']['model']['metrics'],
            [{'name': 'random-sum', 'title': 'random sum'},
             {'name': 'random-avg', 'title': 'random avg'}])

    def test_parse_config_for_no_metrics(self):
        self.assertRaises(ConfigError, GraphWidget.parse_config,
                          {'name': u'some metric'}, {})

    def test_process_backend_response(self):
        def mk_metric(name='some-metric', title='Some Metric',
                      target='some.target', **kwargs):
            metric_config = {
                'target': target,
                'wrapped_target': '%s -- wrapped' % target,
                'null_filter': 'zeroize',
                'metadata': {'name': name, 'title': title}
            }
            metric_config.update(kwargs)
            return GraphiteMetric(**metric_config)

        data = [
            {
                'metadata': {'name': 'metric-1'},
                'datapoints': [{'x': 0, 'y': 0},
                               {'x': 2, 'y': 1},
                               {'x': 3, 'y': 2}]
            }, {
                'metadata': {'name': 'metric-2'},
                'datapoints': [{'x': 5, 'y': 4},
                               {'x':  15, 'y': 1}]
            }, {
                'metadata': {'name': 'metric-3'},
                'datapoints': []
            }
        ]

        result = self.mk_graph_widget().process_backend_response(data)

        expected_metric_data = [
            {
                'name': 'metric-1',
                'datapoints': [{'x': 0, 'y': 0},
                               {'x': 2, 'y': 1},
                               {'x': 3, 'y': 2}]
            }, {
                'name': 'metric-2',
                'datapoints': [{'x': 5, 'y': 4},
                               {'x':  15, 'y': 1}]
            }, {
                'name': 'metric-3',
                'datapoints': []
            }
        ]

        self.assertEqual(result, json.dumps({
            'domain': [0, 15],
            'range': [0, 4],
            'metrics': expected_metric_data
        }))

'''
class StubbedGraphWidgetMetric(GraphWidgetMetric):
    DEFAULTS = {'some_config_option': 'some-config-option'}
'''


'''
class GraphWidgetMetricTestCase(unittest.TestCase):
    @staticmethod def mk_graph_widget_metric(**kwargs):
        kwargs = utils.setdefaults(kwargs, {
            'target': 'some.target',
            'wrapped_target': 'some.target -- wrapped',
            'null_filter': 'some-null-filter',
            'name': 'some-widget',
            'title': 'Some Widget',
            'client_config': {},
            'graphite_url': 'fake-graphite-url',
        })
        return StubbedGraphWidgetMetric(**kwargs)

    def test_parse_config(self):
        config = {
            'name': u'some metric',
            'title': 'Some Metric',
            'target': 'some.random.metric',
        }

        parsed_config = GraphWidgetMetric.parse_config(config, {})
        self.assertEqual(parsed_config['name'], 'some-metric')
        self.assertEqual(parsed_config['title'], 'Some Metric')
        self.assertEqual(parsed_config['client_config'],
                         {'name': 'some-metric', 'title': 'Some Metric'})

    def test_process_datapoints(self):
        metric = self.mk_graph_widget_metric()
        self.assertEqual(
            metric.process_datapoints([[0, 1], [1, 2], [3, 5]]),
            [{'x': 1, 'y': 0}, {'x': 2, 'y': 1}, {'x': 5, 'y': 3}])
'''
