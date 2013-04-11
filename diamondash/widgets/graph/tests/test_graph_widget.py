import time

from twisted.trial import unittest

from diamondash import utils
from diamondash import ConfigError
from diamondash.widgets.graph import GraphWidget
from diamondash.backends.graphite import GraphiteBackend
from diamondash.tests.utils import stub_from_config, ToyBackend


class GraphWidgetTestCase(unittest.TestCase):
    def setUp(self):
        self.stub_time(1340875997)
        self.backend = ToyBackend()
        self.widget = self.mk_graph_widget(
            time_range=86400,
            backend=self.backend)

    def stub_time(self, t):
        self.patch(time, 'time', lambda: t)

    @staticmethod
    def mk_graph_widget(**kwargs):
        kwargs = utils.update_dict({
            'name': 'some-widget',
            'title': 'Some Graph Widget',
            'client_config': {},
            'width': 2,
            'backend': None
        }, kwargs)
        return GraphWidget(**kwargs)

    def test_parse_config(self):
        stub_from_config(GraphiteBackend)

        config = {
            'name': u'test-graph-widget',
            'graphite_url': 'fake_graphite_url',
            'metrics': [
                {'name': u'random sum', 'target':'vumi.random.count.sum'},
                {'name': u'random avg', 'target':'vumi.random.timer.avg'}],
            'time_range': '1d',
            'bucket_size': '1h',
            'null_filter': 'zeroize',
            'metric_defaults': {'some_metric_option': 'some-value'}
        }
        class_defaults = {'SomeWidgetType': "some widget's defaults"}

        parsed_config = GraphWidget.parse_config(config, class_defaults)
        self.assertEqual(parsed_config['time_range'], 86400)

        expected_backend_config = {
            'bucket_size': 3600,
            'null_filter': 'zeroize',
            'metrics': [
                {
                    'some_metric_option': 'some-value',
                    'target':'vumi.random.count.sum',
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
                    'some_metric_option': 'some-value',
                    'target':'vumi.random.timer.avg',
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
        }
        self.assertEqual(parsed_config['backend'],
                         (expected_backend_config, class_defaults))
        self.assertTrue('null_filter' not in parsed_config)

        client_model_config = parsed_config['client_config']['model']
        self.assertEqual(
            client_model_config['metrics'],
            [{'name': 'random-sum', 'title': 'random sum'},
             {'name': 'random-avg', 'title': 'random avg'}])
        self.assertEqual(client_model_config['step'], 3600000)

    def test_parse_config_for_no_metrics(self):
        self.assertRaises(ConfigError, GraphWidget.parse_config,
                          {'name': u'some metric'}, {})

    def assert_snapshot_retrieval(self, backend_res, expected_data,
                                       expected_from_time):
        self.backend.response_data = backend_res
        d = self.widget.get_snapshot()
        self.assertEqual(self.backend.get_data_calls,
                         [{'from_time': expected_from_time}])
        d.addCallback(self.assertEqual, expected_data)
        d.callback(None)
        return d

    def test_snapshot_retrieval(self):
        return self.assert_snapshot_retrieval([
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
        ], {
            'domain': (0, 15),
            'range': (0, 4),
            'metrics': [
                {
                    'name': 'metric-1',
                    'datapoints': [{'x': 0, 'y': 0},
                                   {'x': 2, 'y': 1},
                                   {'x': 3, 'y': 2}]
                },
                {
                    'name': 'metric-2',
                    'datapoints': [{'x': 5, 'y': 4},
                                   {'x':  15, 'y': 1}]
                },
                {
                    'name': 'metric-3',
                    'datapoints': []
                }
            ]
        }, 1340789597)

    def test_snapshot_retrieval_for_empty_datapoints(self):
        return self.assert_snapshot_retrieval([
            {'metadata': {'name': 'metric-1'}, 'datapoints': []},
            {'metadata': {'name': 'metric-2'}, 'datapoints': []},
            {'metadata': {'name': 'metric-3'}, 'datapoints': []}], {
            'domain': (0, 0),
            'range': (0, 0),
            'metrics': [
                {'name': 'metric-1', 'datapoints': []},
                {'name': 'metric-2', 'datapoints': []},
                {'name': 'metric-3', 'datapoints': []}]
        }, 1340789597)

    def test_snapshot_retrieval_for_align_to_start(self):
        self.widget.align_to_start = True
        self.widget.get_snapshot()
        self.assertEqual(self.backend.get_data_calls,
                         [{'from_time': 1340841600}])
