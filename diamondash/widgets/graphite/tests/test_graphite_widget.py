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


class GraphiteWidgetTestCase(unittest.TestCase):
    @staticmethod
    def mk_graphite_widget(**kwargs):
        kwargs = utils.setdefaults(kwargs, {
            'name': 'some-widget',
            'title': 'Some Widget',
            'client_config': {},
            'width': 2,
            'from_time': 3600,
            'bucket_size': 60,
            'graphite_url': 'fake-graphite-url',
        })
        return StubbedGraphiteWidget(**kwargs)

    def test_skip_nulls(self):
        input = [
            [None, 1340875870], [0.075312, 1340875875],
            [0.033274, 1340875885], [None, 1340875890],
            [0.059383, 1340875965], [0.057101, 1340875970],
            [0.056673, 1340875975], [None, 1340875980], [None, 1340875985]]

        expected = [
            [0.075312, 1340875875], [0.033274, 1340875885],
            [0.059383, 1340875965], [0.057101, 1340875970],
            [0.056673, 1340875975]]

        self.assertEqual(GraphiteWidgetMetric.skip_nulls(input), expected)

    def test_zeroize_nulls(self):
        input = [
            [None, 1340875870], [0.075312, 1340875875],
            [0.033274, 1340875885], [None, 1340875890],
            [0.059383, 1340875965], [0.057101, 1340875970],
            [0.056673, 1340875975], [None, 1340875980], [None, 1340875985]]

        expected = [
            [0, 1340875870], [0.075312, 1340875875],
            [0.033274, 1340875885], [0, 1340875890],
            [0.059383, 1340875965], [0.057101, 1340875970],
            [0.056673, 1340875975], [0, 1340875980], [0, 1340875985]]

        self.assertEqual(GraphiteWidgetMetric.zeroize_nulls(input), expected)

    def test_parse_config(self):
        """
        Should parse the config, altering it accordignly to configure the
        widget.
        """
        config = {
            'name': 'test-graphite-widget',
            'graphite_url': 'fake-graphite-url',
        }
        defaults = {'SomeWidgetType': "some widget's defaults"}

        parsed_config = StubbedGraphiteWidget.parse_config(config, defaults)
        self.assertEqual(parsed_config['some_config_option'],
                         'some-config-option')

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
            mock_getPage.assert_called_with('fake-request-url')
            widget.handle_graphite_render_response.assert_called_with(
                json.loads(response_data))
            self.assertEqual(result, 'fake-handled-graphite-render-response')

        response_data = open(resource_filename(
            __name__, 'data/graphite_response_data.json')).read()

        d = Deferred()
        d.addCallback(lambda _: response_data)
        mock_getPage.return_value = d

        widget = self.mk_graphite_widget()
        widget.request_url = 'fake-request-url'
        widget.handle_graphite_render_response = Mock(
            return_value='fake-handled-graphite-render-response')

        deferredResult = widget.handle_render_request(None)
        deferredResult.addCallback(assert_handle_render_request)
        deferredResult.callback(None)
        return deferredResult


class StubbedGraphiteWidgetMetric(GraphiteWidgetMetric):
    DEFAULTS = {'some_config_key': 22, 'some_other_config_key': 3}


class GraphiteWidgetMetricTestCase(unittest.TestCase):
    @patch.object(GraphiteWidgetMetric, 'format_metric_target')
    def test_parse_config(self, mock_format_metric_target):

        config = {
            'target': 'some.target',
            'bucket_size': '1h',
        }
        defaults = {'some_config_key': 23}

        mock_format_metric_target.return_value = 'some.target -- wrapped'
        new_config = StubbedGraphiteWidgetMetric.parse_config(config, defaults)
        mock_format_metric_target.assert_called_with('some.target', 3600)
        self.assertEqual(new_config, {
            'target': 'some.target',
            'bucket_size': 3600,
            'wrapped_target': 'some.target -- wrapped',
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
        mock_filter_nulls = Mock(return_value='null-filtered-datapoints')
        metric = mk_graphite_widget_metric()
        metric.filter_nulls = mock_filter_nulls

        processed_datapoints = metric.process_datapoints(datapoints)
        mock_filter_nulls.assert_called_with('fake-datapoints')
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
    def set_metric(self, metric):
        self.metric = metric


class SingleMetricGraphiteWidgetTestCase(unittest.TestCase):
    @staticmethod
    def mk_single_metric_graphite_widget(**kwargs):
        kwargs = utils.setdefaults(kwargs, {
            'name': 'some-widget',
            'title': 'Some Widget',
            'client_config': {},
            'width': 2,
            'from_time': 3600,
            'time_range': 3600,
            'bucket_size': 60,
            'graphite_url': 'some-url',
            'metric': None
        })
        return StubbedSingleMetricGraphiteWidget(**kwargs)

    @patch.object(GraphiteWidget, 'build_request_url')
    def test__reset_request_url(self, mock_build_request_url):
        metric = Mock()
        metric.wrapped_target = 'wrapped-target'

        widget = self.mk_single_metric_graphite_widget(
            metric=metric, graphite_url='graphite-url', from_time='from-time')
        mock_build_request_url.return_value = 'built-request-url'

        widget._reset_request_url()
        mock_build_request_url.assert_called_with(
            'graphite-url', ['wrapped-target'], 'from-time')
        self.assertEqual(widget.request_url, 'built-request-url')

    def test_set_metric(self):
        widget = self.mk_single_metric_graphite_widget()
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

        metric = mk_graphite_widget_metric(target='some.target')
        metric.process_datapoints = Mock(return_value=[[0, 0], [1, 2], [2, 3]])
        widget = self.mk_single_metric_graphite_widget(metric=metric)

        result = widget.handle_graphite_render_response(data)
        mock_find_dict_by_item.assert_called_with(
            data, 'target', 'some.target')
        metric.process_datapoints.assert_called_with(
            [[0, None], [1, 2], [2, 3]])
        self.assertEqual(result, [[0, 0], [1, 2], [2, 3]])


class StubbedMultiMetricGraphiteWidget(MultiMetricGraphiteWidget):
    def add_metric(self, metric):
        self.metrics.append(metric)
        self.metrics_by_target[metric.target] = metric


class MultiMetricGraphiteWidgetTestCase(unittest.TestCase):
    @staticmethod
    def mk_multi_metric_graphite_widget(**kwargs):
        kwargs = utils.setdefaults(kwargs, {
            'name': 'some-widget',
            'title': 'Some Widget',
            'client_config': {},
            'width': 2,
            'from_time': 3600,
            'bucket_size': 60,
            'graphite_url': 'fake-graphite-url',
            'metrics': []
        })
        return MultiMetricGraphiteWidget(**kwargs)

    @patch.object(GraphiteWidget, 'build_request_url')
    def test__reset_request_url(self, mock_build_request_url):
        metric1 = Mock()
        metric1.wrapped_target = 'metric1-wrapped-target'

        metric2 = Mock()
        metric2.wrapped_target = 'metric2-wrapped-target'

        widget = self.mk_multi_metric_graphite_widget(
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
        metric = mk_graphite_widget_metric(
            target='some.target', wrapped_target='some.wrapped.target')
        widget = self.mk_multi_metric_graphite_widget()
        widget._reset_request_url = Mock()

        widget.add_metric(metric)
        widget._reset_request_url.assert_called()
        self.assertEqual(widget.metrics, [metric])
        self.assertEqual(widget.metrics_by_target['some.target'], metric)

    def test_add_metric(self):
        widget = self.mk_multi_metric_graphite_widget()
        widget._add_metric = Mock()
        widget._reset_request_url = Mock()

        metric = mk_graphite_widget_metric()
        widget.add_metric(metric)
        widget._add_metric.assert_called_with(metric)
        widget._reset_request_url.assert_called()

    def test_add_metrics(self):
        widget = self.mk_multi_metric_graphite_widget()
        widget._add_metric = Mock()
        widget._reset_request_url = Mock()

        widget.add_metrics(['fake-metric-1', 'fake-metric-2'])
        self.assertEqual(
            widget._add_metric.call_args_list,
            [call('fake-metric-1'), call('fake-metric-2')])
        widget._reset_request_url.assert_called()

    def test_handle_graphite_render_response(self):
        data = [
            {
                'target': 'some.target',
                'datapoints': [[0, None], [1, 2], [2, 3]],
            }, {
                'target': 'some.other.target',
                'datapoints': [[0, 3], [2, 6], [4, 9]],
            }, {
                'target': 'yet.another.target',
                'datapoints': [[4, 5], [8, None], [12, 15]],
            }]

        metric1 = mk_graphite_widget_metric(target='some.target')
        metric1.process_datapoints = Mock(
            return_value=[[0, 0], [1, 2], [2, 3]])

        metric2 = mk_graphite_widget_metric(target='yet.another.target')
        metric2.process_datapoints = Mock(return_value=[[4, 5], [12, 15]])

        metric3 = mk_graphite_widget_metric(target='and.another.target')
        metric3.process_datapoints = Mock()

        widget = self.mk_multi_metric_graphite_widget(
            metrics=[metric1, metric2, metric3],
            metrics_by_target={
                'some.target': metric1,
                'yet.another.target': metric2,
                'and.another.target': metric3,
            })

        result = widget.handle_graphite_render_response(data)
        metric1.process_datapoints.assert_called_with(
            [[0, None], [1, 2], [2, 3]])
        metric2.process_datapoints.assert_called_with(
            [[4, 5], [8, None], [12, 15]])
        self.assertEqual(result, [
            {'target': 'some.target', 'datapoints': [[0, 0], [1, 2], [2, 3]]},
            {'target': 'yet.another.target', 'datapoints': [[4, 5], [12, 15]]},
            {'target': 'and.another.target', 'datapoints': []}
        ])


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


def mk_graphite_widget_metric(**kwargs):
    kwargs = utils.setdefaults(kwargs, {
        'target': 'some.target',
        'wrapped_target': 'some.target -- wrapped',
        'null_filter': 'some-null-filter',
        'name': 'some-widget',
        'title': 'some widget',
        'client_config': {},
        'graphite_url': 'fake-graphite-url',
    })
    return StubbedGraphiteWidgetMetric(**kwargs)
