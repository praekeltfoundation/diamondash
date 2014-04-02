import time

from twisted.trial import unittest

from diamondash import utils
from diamondash.config import ConfigError
from diamondash.widgets.lvalue import LValueWidgetConfig, LValueWidget
from diamondash.backends import BadBackendResponseError


def mk_config_data(**overrides):
    return utils.add_dicts({
        'name': 'some-widget',
        'target': 'some.target',
        'title': 'Some LValue Widget',
        'width': 2,
        'time_range': '5s',
        'backend': {'type': 'diamondash.tests.utils.ToyBackend'}
    }, overrides)


class LValueWidgetConfigTestCase(unittest.TestCase):
    def test_parsing(self):
        config = LValueWidgetConfig(mk_config_data())

        self.assertEqual(config['backend']['bucket_size'], 5000)
        self.assertEqual(config['backend']['time_alignment'], 'floor')

        metric_config, = config['backend']['metrics']
        self.assertEqual(metric_config['target'], 'some.target')
        self.assertEqual(metric_config['null_filter'], 'skip')

    def test_parsing_config_for_no_target(self):
        config = mk_config_data()
        del config['target']

        self.assertRaises(
            ConfigError,
            LValueWidgetConfig.parse,
            config)


class LValueWidgetTestCase(unittest.TestCase):
    def setUp(self):
        self.stub_time(1340875997)

    @staticmethod
    def mk_widget(**overrides):
        config = LValueWidgetConfig(mk_config_data(**overrides))
        return LValueWidget(config)

    def stub_time(self, t):
        self.patch(time, 'time', lambda: t)

    def test_snapshot_retrieval(self):
        widget = self.mk_widget()

        widget.backend.set_response([{
            'target': 'some.target',
            'datapoints': [
                {'x': 1340875975000, 'y': 1346269.0},
                {'x': 1340875980000, 'y': 2178309.0},
                {'x': 1340875985000, 'y': 3524578.0},
                {'x': 1340875990000, 'y': 5702887.0},
                {'x': 1340875995000, 'y': 9227465.0},
                {'x': 1340876000000, 'y': 0.0}
            ]
        }])

        deferred_result = widget.get_snapshot()

        def assert_snapshot_retrieval(result):
            self.assertEqual(
                widget.backend.get_requests(),
                [{'from_time': 1340875987000}])

            self.assertEqual(result, {
                'from': 1340875992000,
                'to': 1340875997000,
                'last': 5702887.0,
                'prev': 3524578.0,
            })

        deferred_result.addCallback(assert_snapshot_retrieval)
        return deferred_result

    def test_snapshot_retrieval_align_to_start(self):
        widget = self.mk_widget(align_to_start=True)

        widget.backend.set_response([{
            'target': 'some.target',
            'datapoints': [
                {'x': 1340875975000, 'y': 1346269.0},
                {'x': 1340875980000, 'y': 2178309.0},
                {'x': 1340875985000, 'y': 3524578.0},
                {'x': 1340875990000, 'y': 5702887.0},
                {'x': 1340875995000, 'y': 9227465.0},
                {'x': 1340876000000, 'y': 0.0}
            ]
        }])

        deferred_result = widget.get_snapshot()

        def assert_snapshot_retrieval(result):
            self.assertEqual(
                widget.backend.get_requests(),
                [{'from_time': 1340875985000}])

            self.assertEqual(result, {
                'from': 1340875990000,
                'to': 1340875995000,
                'last': 5702887.0,
                'prev': 3524578.0,
            })

        deferred_result.addCallback(assert_snapshot_retrieval)
        return deferred_result

    def test_snapshot_retrieval_for_default_values(self):
        widget = self.mk_widget(default_value=-1)

        widget.backend.set_response([{
            'target': 'some.target',
            'datapoints': []
        }])

        def check(result):
            self.assertEqual(result, {
                'from': 1340875992000,
                'to': 1340875997000,
                'last': -1,
                'prev': -1,
            })

        d = widget.get_snapshot()
        d.addCallback(check)
        return d

    def test_snapshot_retrieval_for_empty_backend_responses(self):
        widget = self.mk_widget()
        widget.backend.set_response([])
        d = widget.get_snapshot()
        return self.assertFailure(d, BadBackendResponseError)
