from twisted.trial import unittest

from diamondash import utils
from diamondash.widgets.lvalue import LValueWidget
from diamondash.exceptions import ConfigError

from diamondash.tests.utils import (
    stub_classmethod, stub_fn, restore_from_stub)


class LValueWidgetTestCase(unittest.TestCase):
    def test_parse_config(self):
        """
        Should parse the config, altering it accordignly to configure the
        widget.
        """
        def stubbed_insert_defaults_by_key(key, original, defaults):
            original.update({'defaults_inserted': True})
            return original

        def stubbed_parse_interval(interval):
            return 3600

        def stubbed_format_metric_target(cls, target, bucket_size):
            return target, bucket_size

        def stubbed_build_request_url(cls, graphite_url, targets, from_param):
            return graphite_url, targets, from_param

        stub_fn(utils, 'insert_defaults_by_key',
                stubbed_insert_defaults_by_key)
        stub_fn(utils, 'parse_interval', stubbed_parse_interval)

        stub_classmethod(LValueWidget, 'format_metric_target',
                         stubbed_format_metric_target)
        stub_classmethod(LValueWidget, 'build_request_url',
                         stubbed_build_request_url)

        config = LValueWidget.parse_config({
            'name': 'test-lvalue-widget',
            'graphite_url': 'fake_graphite_url',
            'metric': 'vumi.random.count.sum',
            'time_range': '1h',
        })

        self.assertTrue(config['defaults_inserted'])

        self.assertEqual(
            config['request_url'],
            ('fake_graphite_url', [('vumi.random.count.sum', 3600)], 7200))

        restore_from_stub(stubbed_insert_defaults_by_key)
        restore_from_stub(stubbed_parse_interval)
        restore_from_stub(stubbed_format_metric_target)
        restore_from_stub(stubbed_build_request_url)

    def test_parse_config_for_no_metric(self):
        """
        Should raise an exception if the lvalue config has no `metric` key
        """
        config = {
            'name': 'test-lvalue-widget',
            'graphite_url': 'fake_graphite_url',
        }

        self.assertRaises(ConfigError, LValueWidget.parse_config, config)
