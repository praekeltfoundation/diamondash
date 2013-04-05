import json

from twisted.trial import unittest

from diamondash import utils, ConfigError
from diamondash.widgets.lvalue import LValueWidget
from diamondash.backends.graphite import GraphiteBackend
from diamondash.tests.utils import stub_from_config, ToyBackend


class LValueWidgetTestCase(unittest.TestCase):
    @staticmethod
    def mk_lvalue_widget(**kwargs):
        return LValueWidget(**utils.update_dict({
            'name': 'some-widget',
            'title': 'Some Widget',
            'client_config': {},
            'width': 2,
            'time_range': 3600,
            'backend': None,
        }, kwargs))

    def test_parse_config(self):
        """
        Should parse the config, altering it accordingly to configure the
        widget.
        """
        stub_from_config(GraphiteBackend)

        config = {
            'name': u'test-lvalue-widget',
            'target': 'vumi.random.count.sum',
            'time_range': '1h',
        }
        class_defaults = {'SomeWidgetType': "some widget's defaults"}

        parsed_config = LValueWidget.parse_config(config, class_defaults)
        expected_backend_config = {
            'bucket_size': 3600,
            'metrics': [{
                'target': config['target'],
                'null_filter': 'zeroize',
            }]
        }
        self.assertEqual(parsed_config['backend'],
                         (expected_backend_config, class_defaults))
        self.assertEqual(parsed_config['time_range'], 3600)
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
                {'x': 1340875995000, 'y': 9227465.0}]
        }])
        widget = self.mk_lvalue_widget(time_range=3600, backend=backend)
        deferred_result = widget.handle_render_request(None)

        def assert_handled_render_request(result):
            self.assertEqual(backend.get_data_calls, [{'from_time': -7200}])
            self.assertEqual(result, json.dumps({
                'lvalue': 9227465.0,
                'from': 1340875995000,
                'to': 1340875995000 + 3600000 - 1,
                'diff': 9227465.0 - 5702887.0,
                'percentage': 0.61803398874990854,
            }))
        deferred_result.addCallback(assert_handled_render_request)

        deferred_result.callback(None)
        return deferred_result
