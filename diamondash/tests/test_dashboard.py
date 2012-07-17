# -*- coding: utf-8 -*-
"""Tests for diamondash's dashboard"""

import json
from copy import deepcopy

from pkg_resources import resource_filename
from twisted.trial import unittest

from diamondash.dashboard import (
    parse_interval, slugify, format_metric_target,
    parse_config, parse_graph_config, parse_lvalue_config,
    build_client_config, Dashboard, DASHBOARD_DEFAULTS,
    LVALUE_DEFAULTS, GRAPH_DEFAULTS)
from diamondash.exceptions import ConfigError


class DashboardConfigExceptionsTestCase(unittest.TestCase):
    """
    Test cases which should raise ConfigError on erroneous config input data
    """

    def test_from_config_file_not_found(self):
        """
        Should assert an error if the dashboard config file is not found
        """
        self.assertRaises(ConfigError, Dashboard.from_config_file,
                          'tests/non_existent_file.yml')

    def test_no_dashboard_name(self):
        """
        Should assert an error if the dashboard in the config file has no name
        """
        self.assertRaises(ConfigError, Dashboard.from_config_file,
                          'tests/no_dashboard_name.yml')

    def test_no_widget_name(self):
        """Should assert an error if a widget in the config file has no name"""
        self.assertRaises(ConfigError, Dashboard.from_config_file,
                          'tests/no_widget_name.yml')

    def test_no_widget_metrics(self):
        """
        Should assert an error if a widget in the config file
        has no metrics
        """
        self.assertRaises(ConfigError, Dashboard.from_config_file,
                          'tests/no_widget_metrics.yml')

    def test_no_metric_target(self):
        """
        Should assert an error if a metric in the config file has no target
        """
        self.assertRaises(ConfigError, Dashboard.from_config_file,
                          'tests/no_metrics_target.yml')


class DashboardConfigTestCase(unittest.TestCase):
    """
    Test cases which should read in dashboard config
    data and add, parse, modify and replace the input
    where applicable
    """

    TEST_GRAPH_DEFAULTS = {
        'null_filter': 'zeroize',
        'time_range': '1d',
    }

    TEST_LVALUE_DEFAULTS = {
        'time_range': '1h',
    }

    TEST_GRAPH_NAME = 'Some graph widget'
    TEST_GRAPH_NAME_SLUGIFIED = 'some-graph-widget'
    TEST_GRAPH_CONFIG = {
        'name': TEST_GRAPH_NAME_SLUGIFIED,
        'title': TEST_GRAPH_NAME,
        'type': 'graph',
        'time_range': '2d',
        'bucket_size': '1h',
        'metrics': {
            'sum-of-a-salesman': {
                'title': 'Sum of a salesman',
                'target': 'foo.sum',
                'warning_max_threshold': 8,
                'warning_min_threshold': 7,
            },
            'average-of-a-salesman': {
                'title': 'parlez',
                'target': 'foo.avg',
            }
        }
    }
    TEST_GRAPH_CONFIG_PARSED = dict(
        dict(GRAPH_DEFAULTS, **TEST_GRAPH_DEFAULTS), **{
        'name': TEST_GRAPH_NAME_SLUGIFIED,
        'title': TEST_GRAPH_NAME,
        'type': 'graph',
        'time_range': 172800,
        'bucket_size': 3600,
        'metrics': {
            'sum-of-a-salesman': {
                'title': 'Sum of a salesman',
                'null_filter': 'zeroize',
                'original_target': 'foo.sum',
                'target': 'summarize(foo.sum, "3600s", "sum")',
                'warning_max_threshold': 8,
                'warning_min_threshold': 7,
            },
            'average-of-a-salesman': {
                'title': 'parlez',
                'null_filter': 'zeroize',
                'original_target': 'foo.avg',
                'target': 'summarize(foo.avg, "3600s", "avg")',
            }
        },
        'request_url': 'render/?from=-172800s&target=summarize%28foo.sum%2C'
                       '+%223600s%22%2C+%22sum%22%29&target=summarize%28'
                       'foo.avg%2C+%223600s%22%2C+%22avg%22%29&format=json'
    })

    TEST_LVALUE_NAME = 'Some lvalue widget'
    TEST_LVALUE_NAME_SLUGIFIED = 'some-lvalue-widget'
    TEST_LVALUE_CONFIG = {
        'name': TEST_LVALUE_NAME_SLUGIFIED,
        'title': TEST_LVALUE_NAME,
        'type': 'lvalue',
        'time_range': '30m',
        'metrics': ['foo.sum', 'bar.sum']
    }
    TEST_LVALUE_CONFIG_PARSED = dict(
        dict(LVALUE_DEFAULTS, **TEST_LVALUE_DEFAULTS), **{
        'name': TEST_LVALUE_NAME_SLUGIFIED,
        'title': TEST_LVALUE_NAME,
        'type': 'lvalue',
        'time_range': 1800,
        'metrics': [
            {
                'original_target': 'foo.sum',
                'target': 'summarize(foo.sum, "1800s", "sum")',
            },

            {
                'original_target': 'bar.sum',
                'target': 'summarize(bar.sum, "1800s", "sum")',
            }
        ],
        'request_url': 'render/?from=-3600s&target=summarize%28foo.sum%2C'
                       '+%221800s%22%2C+%22sum%22%29&target=summarize%28'
                       'bar.sum%2C+%221800s%22%2C+%22sum%22%29&format=json'
    })

    TEST_CONFIG = {
        'name': 'A dashboard',
        'graph_defaults': TEST_GRAPH_DEFAULTS,
        'lvalue_defaults': TEST_LVALUE_DEFAULTS,
        'widgets': [TEST_GRAPH_CONFIG, TEST_LVALUE_CONFIG]
    }
    TEST_CONFIG_PARSED = dict(DASHBOARD_DEFAULTS, **{
        'name': 'a-dashboard',
        'title': 'A dashboard',
        'graph_defaults': dict(GRAPH_DEFAULTS, **TEST_GRAPH_DEFAULTS),
        'lvalue_defaults': dict(LVALUE_DEFAULTS, **TEST_LVALUE_DEFAULTS),
        'widget_list': [TEST_GRAPH_CONFIG_PARSED, TEST_LVALUE_CONFIG_PARSED],
        'widgets': {
            TEST_GRAPH_NAME_SLUGIFIED: TEST_GRAPH_CONFIG_PARSED,
            TEST_LVALUE_NAME_SLUGIFIED: TEST_LVALUE_CONFIG_PARSED,
        }
    })

    TEST_CLIENT_CONFIG_BUILT = 'var config = %s;' % (json.dumps({
        'name': 'a-dashboard',
        'request_interval': int(DASHBOARD_DEFAULTS['request_interval']) * 1000,
        'widgets': {
            'some-graph-widget': {
                'metrics': {
                    'sum-of-a-salesman': {
                        'title': 'Sum of a salesman',
                        'warning_max_threshold': 8,
                        'warning_min_threshold': 7,
                    },

                    'average-of-a-salesman': {
                        'title': 'parlez'
                    }
                }
            },

            'some-lvalue-widget': {},
        }
    }))

    def test_parse_config(self):
        """
        Should parse a dashboard config,
        applying changes where appropriate
        """
        config = deepcopy(self.TEST_CONFIG)
        result = parse_config(config)
        self.assertEqual(result, self.TEST_CONFIG_PARSED)

    def test_parse_graph_config(self):
        """
        Should parse a graph widget config,
        applying changes where appropriate
        """
        config = deepcopy(self.TEST_GRAPH_CONFIG)
        result = parse_graph_config(config, self.TEST_GRAPH_DEFAULTS)

        self.assertEqual(result, self.TEST_GRAPH_CONFIG_PARSED)

    def test_parse_lvalue_config(self):
        """
        Should parse an lvalue widget config,
        applying changes where appropriate
        """
        config = deepcopy(self.TEST_LVALUE_CONFIG)
        result = parse_lvalue_config(config, self.TEST_LVALUE_DEFAULTS)

        self.assertEqual(result, self.TEST_LVALUE_CONFIG_PARSED)

    def test_build_client_config(self):
        """
        Should build a json string containing configuration
        information necessary for the client side
        """
        result = build_client_config(self.TEST_CONFIG_PARSED)

        self.assertEqual(result, self.TEST_CLIENT_CONFIG_BUILT)

    def test_format_metric_target(self):
        """
        Metric targets should be formatted to be enclosed in a 'summarize()'
        function with the bucket size and aggregation method as arguments.

        The aggregation method should be determined from the
        end of the metric target (avg, max, min, sum).
        """
        def assert_metric_target(target, bucket_size, expected):
            result = format_metric_target(target, bucket_size)
            self.assertEqual(result, expected)

        target = 'vumi.random.count.sum'
        bucket_size = 120
        expected = 'summarize(vumi.random.count.sum, "120s", "sum")'
        assert_metric_target(target, bucket_size, expected)

        target = 'vumi.random.count.avg'
        bucket_size = 620
        expected = 'summarize(vumi.random.count.avg, "620s", "avg")'
        assert_metric_target(target, bucket_size, expected)

        target = 'vumi.random.count.max'
        bucket_size = 120
        expected = 'summarize(vumi.random.count.max, "120s", "max")'
        assert_metric_target(target, bucket_size, expected)

        target = 'integral(vumi.random.count.sum)'
        bucket_size = 120
        expected = 'summarize(integral(vumi.random.count.sum), "120s", "max")'
        assert_metric_target(target, bucket_size, expected)

    def test_slugify(self):
        """Should change 'SomethIng_lIke tHis' to 'something-like-this'"""
        self.assertEqual(slugify('SoMeThing_liKe!tHis'), 'something-like-this')

    def test_widget_title(self):
        """
        Should use the given widget name as the widget title, or set the widget
        title using a title key if it is explicitly specified, even when the
        two different conventions are mixed in a config file
        """
        config = Dashboard.from_config_file(resource_filename(
            __name__, 'widget_title.yml')).config
        self.assertEqual(
            config['widgets']['random-count-sum']['title'], 'random count sum')
        self.assertEqual(config['widgets']['random-timer-average']['title'],
                         'this is an explicit title')

    def test_metric_title(self):
        """
        Should use the given metric name as the metric title, or set the metric
        title using a title key if it is explicitly specified, even when the
        two different conventions are mixed in a config file
        """
        config = Dashboard.from_config_file(resource_filename(
            __name__, 'metric_title.yml')).config
        test_metrics = config['widgets']['test-widget']['metrics']
        self.assertEqual(test_metrics['random-count-sum']['title'],
                         'random count sum')
        self.assertEqual(test_metrics['random-timer-average']['title'],
                         'this is an explicit title')

    def test_parse_interval(self):
        """
        Multiplier-suffixed intervals should be turned into integers correctly.
        """
        self.assertEqual(2, parse_interval(2))
        self.assertEqual(2, parse_interval("2"))
        self.assertEqual(2, parse_interval("2s"))
        self.assertEqual(120, parse_interval("2m"))
        self.assertEqual(7200, parse_interval("2h"))
        self.assertEqual(86400 * 2, parse_interval("2d"))

    def test_graph_time_range(self):
        """
        Should use the given time range if one is provided, otherwise the
        default.
        """
        config = Dashboard.from_config_file(resource_filename(
            __name__, 'graph_time_range.yml')).config

        def assert_time_range(widget_name, time_range):
            self.assertEqual(
                config['widgets'][widget_name]['time_range'], time_range)

        assert_time_range('default-time-range',
                          GRAPH_DEFAULTS['time_range'])
        assert_time_range('explicit-time-range', 1337)
        assert_time_range('suffix-time-range', 7200)
