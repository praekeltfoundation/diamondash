import time
from itertools import count

from twisted.trial import unittest

from diamondash import utils
from diamondash.config import ConfigError
from diamondash.widgets.graph import graph
from diamondash.widgets.graph import GraphWidgetConfig, GraphWidget


def mk_config_data(**overrides):
    return utils.add_dicts({
        'name': u'test-graph-widget',
        'graphite_url': 'fake_graphite_url',
        'metrics': [
            {'name': u'random sum', 'target': 'vumi.random.count.sum'},
            {'name': u'random avg', 'target': 'vumi.random.timer.avg'}],
        'time_range': '1d',
        'bucket_size': '1h',
        'null_filter': 'zeroize',
        'backend': {'type': 'diamondash.tests.utils.ToyBackend'}
    }, overrides)


class GraphWidgetConfigTestCase(unittest.TestCase):
    def setUp(self):
        self.uuid_counter = count()
        self.patch(graph, 'uuid4', lambda: next(self.uuid_counter))

    def test_parsing(self):
        config = GraphWidgetConfig.from_dict(mk_config_data())

        self.assertEqual(config['time_range'], 86400)

        self.assertEqual(config['backend']['bucket_size'], 3600)
        self.assertEqual(config['backend']['null_filter'], 'zeroize')

        m1_config, m2_config = config['backend']['metrics']
        self.assertEqual(m1_config['target'], 'vumi.random.count.sum')
        self.assertEqual(m1_config['metadata'], {
            'id': '0',
            'name': 'random-sum',
            'title': 'random sum',
            'client_config': {
                'id': '0',
                'name': 'random-sum',
                'title': 'random sum',
            },
        })

        self.assertEqual(m2_config['target'], 'vumi.random.timer.avg')
        self.assertEqual(m2_config['metadata'], {
            'id': '1',
            'name': 'random-avg',
            'title': 'random avg',
            'client_config': {
                'id': '1',
                'name': 'random-avg',
                'title': 'random avg',
            },
        })

        self.assertEqual(
            config['client_config']['model']['metrics'],
            [{'id': '0', 'name': 'random-sum', 'title': 'random sum'},
             {'id': '1', 'name': 'random-avg', 'title': 'random avg'}])
        self.assertEqual(config['client_config']['model']['step'], 3600000)

    def test_parsing_for_no_metrics(self):
        config = mk_config_data()
        del config['name']

        self.assertRaises(ConfigError, GraphWidgetConfig.parse, config)


class GraphWidgetTestCase(unittest.TestCase):
    def setUp(self):
        self.uuid_counter = count()
        self.patch(graph, 'uuid4', lambda: next(self.uuid_counter))

        self.stub_time(1340875997)
        self.widget = self.mk_widget()

    def stub_time(self, t):
        self.patch(time, 'time', lambda: t)

    @staticmethod
    def mk_widget(**kwargs):
        config = GraphWidgetConfig.from_dict(mk_config_data(**kwargs))
        return GraphWidget(config)

    def assert_snapshot_retrieval(self, backend_res, expected_data,
                                  expected_from_time):
        self.widget.backend.set_response(backend_res)
        d = self.widget.get_snapshot()
        self.assertEqual(self.widget.backend.get_requests(),
                         [{'from_time': expected_from_time}])
        d.addCallback(self.assertEqual, expected_data)
        d.callback(None)
        return d

    def test_snapshot_retrieval(self):
        return self.assert_snapshot_retrieval([
            {
                'metadata': {'id': '0'},
                'datapoints': [{'x': 0, 'y': 0},
                               {'x': 2, 'y': 1},
                               {'x': 3, 'y': 2}]
            }, {
                'metadata': {'id': '1'},
                'datapoints': [{'x': 5, 'y': 4},
                               {'x':  15, 'y': 1}]
            }, {
                'metadata': {'id': '2'},
                'datapoints': []
            }
        ], {
            'domain': (0, 15000),
            'range': (0, 4),
            'metrics': [
                {
                    'id': '0',
                    'datapoints': [{'x': 0, 'y': 0},
                                   {'x': 2000, 'y': 1},
                                   {'x': 3000, 'y': 2}]
                },
                {
                    'id': '1',
                    'datapoints': [{'x': 5000, 'y': 4},
                                   {'x': 15000, 'y': 1}]
                },
                {
                    'id': '2',
                    'datapoints': []
                }
            ]
        }, 1340789597)

    def test_snapshot_retrieval_for_empty_datapoints(self):
        return self.assert_snapshot_retrieval([
            {'metadata': {'id': '0'}, 'datapoints': []},
            {'metadata': {'id': '1'}, 'datapoints': []},
            {'metadata': {'id': '2'}, 'datapoints': []}], {
            'domain': (0, 0),
            'range': (0, 0),
            'metrics': [
                {'id': '0', 'datapoints': []},
                {'id': '1', 'datapoints': []},
                {'id': '2', 'datapoints': []}]
        }, 1340789597)

    def test_snapshot_retrieval_for_align_to_start(self):
        self.widget.config['align_to_start'] = True
        self.widget.get_snapshot()
        self.assertEqual(self.widget.backend.get_requests(),
                         [{'from_time': 1340841600}])
