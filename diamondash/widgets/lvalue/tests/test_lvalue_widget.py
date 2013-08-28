import json
import time

from twisted.trial import unittest

from diamondash import utils, ConfigError
from diamondash.widgets.lvalue import LValueWidget
from diamondash.backends import BadBackendResponseError
from diamondash.backends.graphite import GraphiteBackend
from diamondash.tests.utils import stub_from_config, ToyBackend


class LValueWidgetTestCase(unittest.TestCase):
    def setUp(self):
        self.stub_time(1340875997)

    @staticmethod
    def mk_lvalue_widget(**kwargs):
        return LValueWidget(**utils.update_dict({
            'name': 'some-widget',
            'title': 'Some Widget',
            'client_config': {},
            'width': 2,
            'time_range': 5,
            'backend': None,
        }, kwargs))

    def stub_time(self, t):
        self.patch(time, 'time', lambda: t)

    def test_parse_config(self):
        """
        Should parse the config, altering it accordingly to configure the
        widget.
        """
        stub_from_config(GraphiteBackend)

        config = {
            'name': u'test-lvalue-widget',
            'target': 'vumi.random.count.sum',
            'time_range': '5s',
        }
        class_defaults = {'SomeWidgetType': "some widget's defaults"}

        parsed_config = LValueWidget.parse_config(config, class_defaults)
        expected_backend_config = {
            'bucket_size': 5,
            'metrics': [{
                'target': config['target'],
                'null_filter': 'skip',
            }]
        }
        self.assertEqual(parsed_config['backend'],
                         (expected_backend_config, class_defaults))
        self.assertEqual(parsed_config['time_range'], 5)
        self.assertTrue('bucket_size' not in parsed_config)

    def test_parse_config_for_no_target(self):
        self.assertRaises(ConfigError, LValueWidget.parse_config, {})

    def test_render_request_handling(self):
        backend = ToyBackend([{
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
        widget = self.mk_lvalue_widget(time_range=5, backend=backend)
        deferred_result = widget.handle_render_request(None)

        def assert_handled_render_request(result):
            self.assertEqual(backend.get_data_calls, [{'from_time': -10}])
            self.assertEqual(result, json.dumps({
                'from': 1340875995000,
                'to': 1340875995000 + 5000 - 1,
                'last': 9227465.0,
                'prev': 5702887.0,
            }))
        deferred_result.addCallback(assert_handled_render_request)

        deferred_result.callback(None)
        return deferred_result

    def test_render_request_handling_for_bad_backend_responses(self):
        def assert_handled_bad_response(datapoints):
            backend = ToyBackend([{
                'target': 'some.target',
                'datapoints': datapoints
            }])
            widget = self.mk_lvalue_widget(time_range=5, backend=backend)
            d = widget.handle_render_request(None)
            return self.assertFailure(d, BadBackendResponseError)

        assert_handled_bad_response([])
        assert_handled_bad_response([{'x': 0, 'y': 0}])
