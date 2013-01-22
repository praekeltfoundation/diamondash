import json
from pkg_resources import resource_filename

from mock import Mock, call, patch
from twisted.internet.defer import Deferred
from twisted.web import client
from twisted.trial import unittest

from diamondash import utils
from diamondash.widgets.graphite import (
    GraphiteWidget, GraphiteWidgetMetric, SingleMetricGraphiteWidget,
    MultiMetricGraphiteWidget, guess_aggregation_method)
from diamondash.exceptions import ConfigError


class StubbedGraphiteWidget(GraphiteWidget):
    DEFAULTS = {'some_config_option': 'some-config-option'}

    def __init__(self, request_url=None):
        self.request_url = request_url


class GraphiteWidgetTestCase(unittest.TestCase):

    @patch.object(utils, 'slugify')
    @patch.object(utils, 'set_key_defaults')
    def test_parse_config(self, mock_set_key_defaults, mock_slugify):
        """
        Should parse the config, altering it accordignly to configure the
        widget.
        """
        config = {
            'name': 'test-graphite-widget',
            'graphite_url': 'fake_graphite_url',
        }
        defaults = {'SomeWidgetType': "some widget's defaults"}
        mock_set_key_defaults.side_effect = lambda k, original, d: original

        parsed_config = StubbedGraphiteWidget.parse_config(config, defaults)
        self.assertEqual(parsed_config['some_config_option'],
                         'some-config-option')
        mock_set_key_defaults.assert_called()

    def test_parse_config_for_no_graphite_url(self):
        self.assertRaises(ConfigError, StubbedGraphiteWidget.parse_config,
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


class StubbedGraphiteWidgetMetric(GraphiteWidgetMetric):
    DEFAULTS = {'some_config_key': 22, 'some_other_config_key': 3}

    def __init__(self, target=None, wrapped_target=None, null_filter=None):
        self.target = target
        self.wrapped_target = wrapped_target
        self.filter_nulls = null_filter


class GraphiteWidgetMetricTestCase(unittest.TestCase):

    @patch.object(utils, 'parse_interval')
    @patch.object(GraphiteWidgetMetric, 'format_metric_target')
    def test_parse_config(self, mock_format_metric_target,
                          mock_parse_interval):

        config = {
            'target': 'some.random.target',
            'bucket_size': '1h',
        }
        defaults = {'some_config_key': 23}

        mock_parse_interval.return_value = 3600
        mock_format_metric_target.return_value = 'wrapped-target'

        new_config = StubbedGraphiteWidgetMetric.parse_config(config, defaults)
        mock_parse_interval.assert_called_with('1h')
        mock_format_metric_target.assert_called_with(
            'some.random.target', 3600)
        self.assertEqual(new_config, {
            'target': 'some.random.target',
            'bucket_size': 3600,
            'wrapped_target': 'wrapped-target',
            'some_config_key': 23,
            'some_other_config_key': 3,
        })

    def test_parse_config_for_no_bucket_size(self):
        config = {'target': 'some.random.target'}
        new_config = GraphiteWidgetMetric.parse_config(config, {})
        self.assertEqual(new_config['wrapped_target'], 'some.random.target')

    def test_parse_config_for_no_target(self):
        self.assertRaises(ConfigError, GraphiteWidgetMetric.parse_config,
                          {}, {})

    def test_process_datapoints(self):
        datapoints = 'fake-datapoints'
        mock_null_filter = Mock(return_value='null-filtered-datapoints')
        metric = StubbedGraphiteWidgetMetric(null_filter=mock_null_filter)

        processed_datapoints = metric.process_datapoints(datapoints)
        mock_null_filter.assert_called_with('fake-datapoints')
        self.assertEqual(processed_datapoints, 'null-filtered-datapoints')

    def test_format_metric_target(self):
        """
        Metric targets should be formatted to be enclosed in a 'summarize()'
        function with the bucket size and aggregation method as arguments.

        The aggregation method should be determined from the
        end of the metric target (avg, max, min, sum).
        """
        def assert_metric_target(target, bucket_size, expected):
            result = GraphiteWidgetMetric.format_metric_target(
                target, bucket_size)
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


class StubbedSingleMetricGraphiteWidget(SingleMetricGraphiteWidget):
    def __init__(self, metric=None, graphite_url=None, from_time=None):
        self.metric = metric
        self.graphite_url = graphite_url
        self.from_time = from_time


class SingleMetricGraphiteWidgetTestCase(unittest.TestCase):

    @patch.object(GraphiteWidget, 'build_request_url')
    def test__reset_request_url(self, mock_build_request_url):
        metric = Mock()
        metric.wrapped_target = 'wrapped-target'

        widget = StubbedSingleMetricGraphiteWidget(
            metric, 'graphite-url', 'from-time')
        mock_build_request_url.return_value = 'built-request-url'

        widget._reset_request_url()
        mock_build_request_url.assert_called_with(
            'graphite-url', ['wrapped-target'], 'from-time')
        self.assertEqual(widget.request_url, 'built-request-url')

    def test_set_metric(self):
        widget = StubbedSingleMetricGraphiteWidget()
        widget._reset_request_url = Mock()

        widget.set_metric('some-metric')
        self.assertEqual(widget.metric, 'some-metric')
        widget._reset_request_url.assert_called()

    @patch.object(utils, 'find_dict_by_item')
    def test_handle_graphite_render_response(self, mock_find_dict_by_item):
        data = [
            {
                'target': 'some.target',
                'datapoints': [[0, None], [1, 2], [2, 3]]
            }, {
                'target': 'some.other.target',
                'datapoints': [[0, 2], [1, 4], [3, 6]]
            }
        ]

        mock_find_dict_by_item.return_value = {
            'target': 'some.target',
            'datapoints': [[0, None], [1, 2], [2, 3]]
        }

        metric = StubbedGraphiteWidgetMetric(target='some.target')
        metric.process_datapoints = Mock(return_value=[[0, 0], [1, 2], [2, 3]])
        widget = StubbedSingleMetricGraphiteWidget(metric=metric)

        result = widget.handle_graphite_render_response(data)
        mock_find_dict_by_item.assert_called_with(
            data, 'target', 'some.target')
        metric.process_datapoints.assert_called_with(
            [[0, None], [1, 2], [2, 3]])
        self.assertEqual(result, [[0, 0], [1, 2], [2, 3]])


class StubbedMultiMetricGraphiteWidget(MultiMetricGraphiteWidget):
    def __init__(self, metrics=[], metrics_by_target={},
                 graphite_url=None, from_time=None):
        self.metrics = metrics
        self.metrics_by_target = metrics_by_target

        self.graphite_url = graphite_url
        self.from_time = from_time


class MultiMetricGraphiteWidgetTestCase(unittest.TestCase):

    @patch.object(GraphiteWidget, 'build_request_url')
    def test__reset_request_url(self, mock_build_request_url):
        metric1 = Mock()
        metric1.wrapped_target = 'metric1-wrapped-target'

        metric2 = Mock()
        metric2.wrapped_target = 'metric2-wrapped-target'

        widget = StubbedMultiMetricGraphiteWidget(
            metrics=[metric1, metric2],
            graphite_url='graphite-url',
            from_time='from-time')
        mock_build_request_url.return_value = 'built-request-url'

        widget._reset_request_url()
        mock_build_request_url.assert_called_with(
            'graphite-url',
            ['metric1-wrapped-target', 'metric2-wrapped-target'],
            'from-time')
        self.assertEqual(widget.request_url, 'built-request-url')

    def test__add_metric(self):
        metric = StubbedGraphiteWidgetMetric(
            target='some-target', wrapped_target='some-wrapped-target')
        widget = StubbedMultiMetricGraphiteWidget(metrics=[])
        widget._reset_request_url = Mock()

        widget.add_metric(metric)
        widget._reset_request_url.assert_called()
        self.assertEqual(widget.metrics, [metric])
        self.assertEqual(widget.metrics_by_target['some-target'], metric)

    def test_add_metric(self):
        widget = StubbedMultiMetricGraphiteWidget()
        widget._add_metric = Mock()
        widget._reset_request_url = Mock()

        widget.add_metric('fake-metric')
        widget._add_metric.assert_called_with('fake-metric')
        widget._reset_request_url.assert_called()

    def test_add_metrics(self):
        widget = StubbedMultiMetricGraphiteWidget()
        widget._add_metric = Mock()
        widget._reset_request_url = Mock()

        widget.add_metrics(['fake-metric-1', 'fake-metric-2'])
        self.assertEqual(
            widget._add_metric.call_args_list,
            [call('fake-metric-1'), call('fake-metric-2')])
        widget._reset_request_url.assert_called()


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
