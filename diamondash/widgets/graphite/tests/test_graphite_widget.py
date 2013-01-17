from twisted.trial import unittest

from diamondash import utils
from diamondash.widgets.graphite import (
    GraphiteWidget, guess_aggregation_method)
from diamondash.exceptions import ConfigError

from diamondash.tests.utils import stub_fn, restore_from_stub


class GraphiteWidgetTestCase(unittest.TestCase):
    def test_parse_config(self):
        """
        Should parse the config, altering it accordignly to configure the
        widget.
        """
        def stubbed_insert_defaults_by_key(key, original, defaults):
            original.update({'defaults_inserted': True})
            return original

        stub_fn(utils, 'insert_defaults_by_key',
                stubbed_insert_defaults_by_key)

        config = GraphiteWidget.parse_config({
            'name': 'test-graphite-widget',
            'graphite_url': 'fake_graphite_url',
        })

        self.assertTrue(config['defaults_inserted'])
        self.assertEqual(config['request_url'], None)

        restore_from_stub(stubbed_insert_defaults_by_key)

    def test_parse_config_for_no_graphite_url(self):
        self.assertRaises(ConfigError, GraphiteWidget.parse_config,
                          {'name': 'test-graphite-widget'})

    def test_build_request_url(self):
        """
        Should build a render request url that can be used to get metric data
        from graphite.
        """
        def assert_request_url(graphite_url, targets, from_param, expected):
            request_url = GraphiteWidget.build_request_url(graphite_url,
                                                           targets, from_param)
            self.assertEqual(request_url, expected)

        assert_request_url(
            'http://127.0.0.1/',
            ['vumi.random.count.max'],
            1000,
            ('http://127.0.0.1/render/?from=-1000s'
            '&target=vumi.random.count.max&format=json'))

        assert_request_url(
            'http://127.0.0.1',
            ['vumi.random.count.max', 'vumi.random.count.avg'],
            2000,
            ('http://127.0.0.1/render/?from=-2000s'
             '&target=vumi.random.count.max'
             '&target=vumi.random.count.avg&format=json'))

        assert_request_url(
            'http://someurl.com/',
            ['vumi.random.count.max',
             'summarize(vumi.random.count.sum, "120s", "sum")'],
            3000,
            ('http://someurl.com/render/?from=-3000s'
             '&target=vumi.random.count.max'
             '&target=summarize%28vumi.random.count.sum'
             '%2C+%22120s%22%2C+%22sum%22%29&format=json'))

    def test_format_metric_target(self):
        """
        Metric targets should be formatted to be enclosed in a 'summarize()'
        function with the bucket size and aggregation method as arguments.

        The aggregation method should be determined from the
        end of the metric target (avg, max, min, sum).
        """
        def assert_metric_target(target, bucket_size, expected):
            result = GraphiteWidget.format_metric_target(target, bucket_size)
            self.assertEqual(result, expected)

        target = 'vumi.random.count.sum'
        bucket_size = 120
        expected = (
            'alias(summarize(vumi.random.count.sum, "120s", "sum"), '
            '"vumi.random.count.sum")')
        assert_metric_target(target, bucket_size, expected)

        target = 'vumi.random.count.avg'
        bucket_size = 620
        expected = (
            'alias(summarize(vumi.random.count.avg, "620s", "avg"), '
            '"vumi.random.count.avg")')
        assert_metric_target(target, bucket_size, expected)

        target = 'vumi.random.count.max'
        bucket_size = 120
        expected = (
            'alias(summarize(vumi.random.count.max, "120s", "max"), '
            '"vumi.random.count.max")')
        assert_metric_target(target, bucket_size, expected)

        target = 'integral(vumi.random.count.sum)'
        bucket_size = 120
        expected = (
            'alias(summarize(integral(vumi.random.count.sum), "120s", "max"), '
            '"integral(vumi.random.count.sum)")')
        assert_metric_target(target, bucket_size, expected)


class GraphiteWidgetUtilsTestCase(unittest.TestCase):
    def test_guess_aggregation_method(self):
        """
        Metric targets should be formatted to be enclosed in a 'summarize()'
        function with the bucket size and aggregation method as arguments.

        The aggregation method should be determined from the
        end of the metric target (avg, max, min, sum).
        """
        def assert_agg_method(target, expected):
            result = guess_aggregation_method(target)
            self.assertEqual(result, expected)

        assert_agg_method("foo.max", "max")
        assert_agg_method("foo.min", "min")
        assert_agg_method("integral(foo.sum)", "max")
        assert_agg_method("sum(foo.min)", "min")
        assert_agg_method('somefunc("foo.max", foo.min)', "min")
        assert_agg_method('foo(bar(baz.min), baz.max)', "min")
        assert_agg_method('foo(bar("baz.min"), baz.max)', "max")
