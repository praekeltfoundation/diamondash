import json
from pkg_resources import resource_filename

from mock import Mock, patch
from twisted.internet.defer import Deferred
from twisted.web import client
from twisted.trial import unittest

from diamondash import utils
from diamondash.widgets.graphite import (
    GraphiteWidget, guess_aggregation_method)
from diamondash.exceptions import ConfigError


class StubbedGraphiteWidget(GraphiteWidget):
    def __init__(self, request_url=None):
        self.request_url = request_url


class GraphiteWidgetTestCase(unittest.TestCase):

    @patch.object(utils, 'slugify')
    @patch.object(utils, 'insert_defaults_by_key')
    def test_parse_config(self, mock_insert_defaults_by_key, mock_slugify):
        """
        Should parse the config, altering it accordignly to configure the
        widget.
        """
        config = {
            'name': 'test-graphite-widget',
            'graphite_url': 'fake_graphite_url',
        }
        defaults = {'SomeWidgetType': "some widget's defaults"}
        mock_insert_defaults_by_key.side_effect = (
            lambda key, original, defaults: original)

        parsed_config = GraphiteWidget.parse_config(config, defaults)
        self.assertTrue(mock_insert_defaults_by_key.called)
        self.assertEqual(parsed_config['request_url'], None)

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

    @patch.object(client, 'getPage')
    def test_handle_render_request(self, mock_getPage):
        """
        Should send a render request to graphite, decode the json response,
        handle the decoded response and return the result.
        """
        def assert_handle_render_request(result):
            mock_getPage.assert_called_with('fake_request_url')
            widget.handle_graphite_render_response.assert_called_with(
                json.loads(response_data))
            self.assertEqual(result, 'fake_handled_graphite_render_response')

        response_data = open(resource_filename(
            __name__, 'data/graphite_response_data.json')).read()

        d = Deferred()
        d.addCallback(lambda _: response_data)
        mock_getPage.return_value = d

        widget = StubbedGraphiteWidget(request_url='fake_request_url')
        widget.handle_graphite_render_response = Mock(
            return_value='fake_handled_graphite_render_response')

        deferredResult = widget.handle_render_request(None)
        deferredResult.addCallback(assert_handle_render_request)
        deferredResult.callback(None)
        return deferredResult


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
