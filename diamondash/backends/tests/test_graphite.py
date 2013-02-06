import json

from mock import call, patch, Mock
from twisted.internet.defer import Deferred
from twisted.web import client
from twisted.trial import unittest

from diamondash import utils, ConfigError
from diamondash.backends.graphite import (
    GraphiteBackend, GraphiteMetric, guess_aggregation_method)


class GraphiteBackendTestCase(unittest.TestCase):
    def mk_graphite_backend(self, **kwargs):
        def mock_add_metrics(self, metrics):
            for metric in metrics:
                self._add_metric(metric)

        patcher = self.patch(GraphiteBackend, 'add_metrics', mock_add_metrics)
        kwargs = utils.setdefaults(kwargs, {
            'from_time': 3600,
            'graphite_url': 'fake-graphite-url',
            'metrics': [],
        })
        backend = GraphiteBackend(**kwargs)
        backend.request_url = 'fake-built-request-url'
        patcher.restore()

        return backend

    @patch.object(GraphiteMetric, 'from_config')
    def test_parse_config(self, mock_graphite_metric_from_config):
        mock_graphite_metric_from_config.side_effect = (
            lambda config, class_defaults: "%s -- created" % config)
        config = {
            'graphite_url': 'fake-graphite-url',
            'from_time': '1h',
            'metrics': ['fake-metric-1', 'fake-metric-2']
        }
        class_defaults = {'SomeType': "some default value"}

        parsed_config = GraphiteBackend.parse_config(config, class_defaults)
        self.assertEqual(
            mock_graphite_metric_from_config.call_args_list,
            [call('fake-metric-1', class_defaults),
             call('fake-metric-2', class_defaults)]
        )
        self.assertEqual(parsed_config, {
            'graphite_url': 'fake-graphite-url',
            'from_time': 3600,
            'metrics': ['fake-metric-1 -- created', 'fake-metric-2 -- created']
        })

    def test_build_request_url(self):
        """
        Should build a render request url that can be used to get metric data
        from graphite.
        """
        def assert_request_url(graphite_url, from_time, targets, expected):
            request_url = GraphiteBackend.build_request_url(
                graphite_url, from_time, targets)
            self.assertEqual(request_url, expected)

        assert_request_url(
            'http://127.0.0.1/',
            1000,
            ['vumi.random.count.max'],
            ('http://127.0.0.1/render/?from=-1000s'
            '&target=vumi.random.count.max&format=json'))

        assert_request_url(
            'http://127.0.0.1',
            2000,
            ['vumi.random.count.max', 'vumi.random.count.avg'],
            ('http://127.0.0.1/render/?from=-2000s'
             '&target=vumi.random.count.max'
             '&target=vumi.random.count.avg&format=json'))

        assert_request_url(
            'http://someurl.com/',
            3000,
            ['vumi.random.count.max',
             'summarize(vumi.random.count.sum, "120s", "sum")'],
            ('http://someurl.com/render/?from=-3000s'
             '&target=vumi.random.count.max'
             '&target=summarize%28vumi.random.count.sum'
             '%2C+%22120s%22%2C+%22sum%22%29&format=json'))

    def test_add_metric(self):
        backend = self.mk_graphite_backend(
            graphite_url='fake-graphite-url', from_time=3600)
        backend.build_request_url = Mock(
            return_value='new-fake-built-request-url')

        metric = mk_graphite_metric(target='some.target')
        backend.add_metric(metric)

        self.assertEqual(backend.metrics, [metric])
        self.assertEqual(backend.request_url, 'new-fake-built-request-url')
        backend.build_request_url.assert_called_with(
            'fake-graphite-url', 3600, ['some.target -- wrapped'])

    def test_add_metrics(self):
        backend = self.mk_graphite_backend(
            graphite_url='fake-graphite-url', from_time=3600)
        backend.build_request_url = Mock(
            return_value='new-fake-built-request-url')

        m1 = mk_graphite_metric(target='some.target')
        m2 = mk_graphite_metric(target='some.other.target')
        backend.add_metrics([m1, m2])

        self.assertEqual(backend.metrics, [m1, m2])
        self.assertEqual(backend.request_url, 'new-fake-built-request-url')
        backend.build_request_url.assert_called_with(
            'fake-graphite-url',
            3600,
            ['some.target -- wrapped', 'some.other.target -- wrapped'])

    @patch.object(client, 'getPage')
    def test_get_data(self, mock_getPage):
        def assert_handle_render_request(result):
            mock_getPage.assert_called_with('fake-request-url')
            m1.process_datapoints.assert_called_with(m1_raw_datapoints)
            m2.process_datapoints.assert_called_with(m2_raw_datapoints)
            self.assertEqual(
                result,
                [{'metadata': {'some-field': 'lorem'},
                  'datapoints': m1_processed_datapoints},
                 {'metadata': {'some-field': 'ipsum'},
                  'datapoints': m2_processed_datapoints}])

        m1 = mk_graphite_metric(
            target='some.target',
            metadata={'some-field': 'lorem'})
        m1_raw_datapoints = [
            [None, 1342382400],
            [0.04924959844054583, 1342386000],
            [0.05052084873949578, 1342389600]]
        m1_processed_datapoints = [
            {'x': 1342382400, 'y': 0},
            {'x': 1342386000, 'y': 0.04924959844054583},
            {'x': 1342389600, 'y': 0.05052084873949578}]
        m1.process_datapoints = Mock(return_value=m1_processed_datapoints)

        m2 = mk_graphite_metric(
            target='some.other.target',
            metadata={'some-field': 'ipsum'})
        m2_raw_datapoints = [
            [None, 1342382400],
            [1281.0, 1342386000],
            [285.0, 1342389600]]
        m2_processed_datapoints = [
            {'x': 0, 'y': 0},
            {'x': 1342386000, 'y': 1281.0},
            {'x': 1342389600, 'y': 285.0}]
        m2.process_datapoints = Mock(return_value=m2_processed_datapoints)

        response_data = json.dumps([
            {"target": "some.target", "datapoints": m1_raw_datapoints},
            {"target": "some.other.target", "datapoints": m2_raw_datapoints}])

        d = Deferred()
        d.addCallback(lambda _: response_data)
        mock_getPage.return_value = d

        backend = self.mk_graphite_backend(
            graphite_url='fake-graphite-url',
            from_time=3600,
            metrics=[m1, m2])
        backend.request_url = 'fake-request-url'

        deferredResult = backend.get_data()
        deferredResult.addCallback(assert_handle_render_request)
        deferredResult.callback(None)
        return deferredResult

    @patch.object(client, 'getPage')
    def test_get_data_for_kwargs(self, mock_getPage):
        def assert_handle_render_request(result):
            backend.build_request_url.assert_called_with(
                'fake-custom-graphite-url',
                7200,
                ['some.target -- wrapped', 'some.other.target -- wrapped'])
            mock_getPage.assert_called_with('new-fake-built-request-url')

        d = Deferred()
        d.addCallback(lambda _: 'fake-getPage-response')
        mock_getPage.return_value = d

        metrics = [mk_graphite_metric(target='some.target'),
                   mk_graphite_metric(target='some.other.target')]
        backend = self.mk_graphite_backend(
            graphite_url='fake-graphite-url', metrics=metrics)
        backend.handle_graphite_response = Mock()  # covered in test_get_data()
        backend.build_request_url = Mock(
            return_value='new-fake-built-request-url')

        deferredResult = backend.get_data(
            graphite_url='fake-custom-graphite-url',
            from_time='2h')
        deferredResult.addCallback(assert_handle_render_request)
        deferredResult.callback(None)
        return deferredResult


class GraphiteMetricTestCase(unittest.TestCase):
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

        self.assertEqual(GraphiteMetric.skip_nulls(input), expected)

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

        self.assertEqual(GraphiteMetric.zeroize_nulls(input), expected)

    @patch.object(GraphiteMetric, 'format_metric_target')
    def test_parse_config(self, mock_format_metric_target):
        config = {
            'target': 'some.target',
            'bucket_size': '1h',
            'null_filter': 'zeroize',
            'metadata': {'name': 'luke-the-metric'}
        }
        class_defaults = {'SomeType': "some default value"}

        mock_format_metric_target.return_value = 'some.target -- wrapped'
        new_config = GraphiteMetric.parse_config(config, class_defaults)
        mock_format_metric_target.assert_called_with('some.target', 3600)
        self.assertEqual(new_config, {
            'target': 'some.target',
            'bucket_size': 3600,
            'null_filter': 'zeroize',
            'wrapped_target': 'some.target -- wrapped',
            'metadata': {'name': 'luke-the-metric'}
        })

    def test_parse_config_for_no_bucket_size(self):
        config = {'target': 'some.random.target'}
        new_config = GraphiteMetric.parse_config(config, {})
        self.assertEqual(new_config['wrapped_target'], 'some.random.target')

    def test_parse_config_for_no_target(self):
        self.assertRaises(ConfigError, GraphiteMetric.parse_config, {}, {})

    def test_process_datapoints(self):
        datapoints = [
            [None, 1342382400],
            [0.04924959844054583, 1342386000],
            [0.05052084873949578, 1342389600]]
        null_filtered_datapoints = [
            [0, 1342382400],
            [0.04924959844054583, 1342386000],
            [0.05052084873949578, 1342389600]]
        mock_filter_nulls = Mock(return_value=null_filtered_datapoints)
        metric = mk_graphite_metric()
        metric.filter_nulls = mock_filter_nulls

        expected_processed_datapoints = [
            {'x': 1342382400, 'y': 0},
            {'x': 1342386000, 'y': 0.04924959844054583},
            {'x': 1342389600, 'y': 0.05052084873949578}]
        processed_datapoints = metric.process_datapoints(datapoints)
        mock_filter_nulls.assert_called_with(datapoints)
        self.assertEqual(processed_datapoints, expected_processed_datapoints)

    def test_format_metric_target(self):
        """
        Metric targets should be formatted to be enclosed in a 'summarize()'
        function with the bucket size and aggregation method as arguments.

        The aggregation method should be determined from the
        end of the metric target (avg, max, min, sum).
        """
        def assert_metric_target(target, bucket_size, expected):
            result = GraphiteMetric.format_metric_target(
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


class GraphiteUtilsTestCase(unittest.TestCase):
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


def mk_graphite_metric(target='some.target', **kwargs):
    kwargs = utils.setdefaults(kwargs, {
        'target': target,
        'wrapped_target': '%s -- wrapped' % target,
        'null_filter': 'zeroize',
        'metadata': {},
    })
    return GraphiteMetric(**kwargs)
