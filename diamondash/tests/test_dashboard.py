# -*- coding: utf-8 -*-
"""Tests for diamondash's dashboard"""

from pkg_resources import resource_filename
from twisted.trial import unittest

from diamondash.dashboard import (
    parse_interval, slugify, format_metric_target,
    Dashboard, GRAPH_DEFAULTS)
from diamondash.exceptions import ConfigError


class DashboardTestCase(unittest.TestCase):

    def test_slugify(self):
        """Should change 'SomethIng_lIke tHis' to 'something-like-this'"""
        self.assertEqual(slugify('SoMeThing_liKe!tHis'), 'something-like-this')

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

    def test_from_config_file_not_found(self):
        """
        Should assert an error if the dashboard in the config file has no name
        """
        self.assertRaises(ConfigError, Dashboard.from_config_file,
                          'tests/non_existent_file.yml')

    def test_no_dashboard_name(self):
        """
        Should assert an error if the dashboard in the config file has no name
        """
        self.assertRaises(ConfigError, Dashboard.from_config_file,
                          'tests/no_dashboard_name.yml')

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

    def test_no_widget_metrics(self):
        """Should assert an error if a widget in the config file has no name"""
        self.assertRaises(ConfigError, Dashboard.from_config_file,
                          'tests/no_widget_metrics.yml')

    def test_no_metric_target(self):
        """
        Should assert an error if a metric in the config file has no target
        """
        self.assertRaises(ConfigError, Dashboard.from_config_file,
                          'tests/no_metrics_target.yml')

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

    def test_graph_time_range(self):
        """
        Should use the given time range if one is provided, otherwise the
        default.
        """
        config = Dashboard.from_config_file(resource_filename(
            __name__, 'graph_time_range.yml')).config

        def assert_time_range(widget_name, render_period):
            self.assertEqual(
                config['widgets'][widget_name]['time_range'], render_period)

        assert_time_range('default-time-range',
                             GRAPH_DEFAULTS['time_range'])
        assert_time_range('explicit-time-range', 1337)
        assert_time_range('suffix-time-range', 7200)
