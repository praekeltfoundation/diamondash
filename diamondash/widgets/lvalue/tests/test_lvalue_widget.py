import json

from twisted.trial import unittest

from diamondash import utils
from diamondash.widgets.lvalue import LValueWidget
from diamondash.backends.graphite import GraphiteBackend
from diamondash.tests import helpers


class LValueWidgetTestCase(unittest.TestCase):
    @staticmethod
    def mk_lvalue_widget(**kwargs):
        kwargs = utils.update_dict(kwargs, {
            'name': 'some-widget',
            'title': 'Some Widget',
            'client_config': {},
            'width': 2,
            'time_range': 3600,
            'backend': None
        })
        return LValueWidget(**kwargs)

    def test_parse_config(self):
        """
        Should parse the config, altering it accordingly to configure the
        widget.
        """
        helpers.stub_from_config(GraphiteBackend)

        config = {
            'name': u'test-lvalue-widget',
            'target': 'vumi.random.count.sum',
            'time_range': '1h',
        }
        class_defaults = {'SomeWidgetType': "some widget's defaults"}

        parsed_config = LValueWidget.parse_config(config, class_defaults)
        expected_backend_config = {
            'from_time': 7200,
            'metrics': [{
                'target': config['target'],
                'bucket_size': 3600,
                'null_filter': 'zeroize',
            }]
        }
        self.assertEqual(parsed_config['backend'],
                         (expected_backend_config, class_defaults))
        self.assertEqual(parsed_config['time_range'], 3600)

    def test_process_backend_response(self):
        data = [
            {
                'target': 'some.target',
                'datapoints': [
                    {'x': 1340875975, 'y': 1346269.0},
                    {'x': 1340875980, 'y': 2178309.0},
                    {'x': 1340875985, 'y': 3524578.0},
                    {'x': 1340875990, 'y': 5702887.0},
                    {'x': 1340875995, 'y': 9227465.0}]
            }
        ]
        widget = self.mk_lvalue_widget(time_range=3600)

        results = widget.process_backend_response(data)
        self.assertEqual(results, json.dumps({
            'lvalue': 9227465.0,
            'from': 1340875995,
            'to': 1340875995 + 3600 - 1,
            'diff': 9227465.0 - 5702887.0,
            'percentage': 0.61803398874990854,
        }))
