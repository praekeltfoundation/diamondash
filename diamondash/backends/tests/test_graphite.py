import json

from mock import Mock
from twisted.internet.defer import Deferred
from twisted.web import client
from twisted.trial import unittest

from diamondash import utils, ConfigError
from diamondash.backends.graphite import (
    GraphiteBackend, GraphiteMetric, guess_aggregation_method)
from diamondash.tests import helpers


def mk_graphite_metric(target='some.target', **kwargs):
    wrapped_target = (
        'alias(summarize(%s, "3600s", "avg"), "%s")' % (target, target))
    kwargs = utils.setdefaults(kwargs, {
        'target': target,
        'wrapped_target': wrapped_target,
        'null_filter': 'zeroize',
        'metadata': {},
    })
    return GraphiteMetric(**kwargs)


class GraphiteBackendTestCase(unittest.TestCase):
    M1_RAW_DATAPOINTS = [
        [None, 1342382400],
        [0.04924959844054583, 1342386000],
        [0.05052084873949578, 1342389600]]
    M1_PROCESSED_DATAPOINTS = [
        {'x': 1342382400, 'y': 0},
        {'x': 1342386000, 'y': 0.04924959844054583},
        {'x': 1342389600, 'y': 0.05052084873949578}]

    M2_RAW_DATAPOINTS = [
        [None, 1342382400],
        [1281.0, 1342386000],
        [285.0, 1342389600]]
    M2_PROCESSED_DATAPOINTS = [
        {'x': 1342382400, 'y': 0},
        {'x': 1342386000, 'y': 1281.0},
        {'x': 1342389600, 'y': 285.0}]

    def mk_graphite_backend(self, **kwargs):
        kwargs = utils.setdefaults(kwargs, {
            'from_time': 3600,
            'graphite_url': 'http://some-graphite-url.moc:8080/',
            'metrics': [],
        })
        backend = GraphiteBackend(**kwargs)
        return backend

    def stub_getPage(self, response_data):
        d = Deferred()
        d.addCallback(lambda _: response_data)
        client.getPage = Mock(return_value=d)

    def test_parse_config(self):
        helpers.stub_from_config(GraphiteMetric)
        config = {
            'graphite_url': 'http://some-graphite-url.moc:8080/',
            'from_time': '1h',
            'metrics': ['fake-metric-1', 'fake-metric-2']
        }
        class_defaults = {'SomeType': "some default value"}

        parsed_config = GraphiteBackend.parse_config(config, class_defaults)
        self.assertEqual(parsed_config, {
            'graphite_url': 'http://some-graphite-url.moc:8080/',
            'from_time': 3600,
            'metrics': [
                ('fake-metric-1', class_defaults),
                ('fake-metric-2', class_defaults)]
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

    def test_get_data(self):
        m1 = mk_graphite_metric(
            target='some.target',
            metadata={'some-field': 'lorem'})
        m2 = mk_graphite_metric(
            target='some.other.target',
            metadata={'some-field': 'ipsum'})

        response_data = json.dumps([
            {"target": "some.target",
             "datapoints": self.M1_RAW_DATAPOINTS},
            {"target": "some.other.target",
             "datapoints": self.M2_RAW_DATAPOINTS}])
        self.stub_getPage(response_data)

        backend = self.mk_graphite_backend(
            graphite_url='http://some-graphite-url.moc:8080/',
            from_time=3600,
            metrics=[m1, m2])
        deferredResult = backend.get_data()

        def assert_handle_render_request(result):
            client.getPage.assert_called_with(
                "http://some-graphite-url.moc:8080/render/?from=-3600s"
                "&target=alias%28summarize%28some.target%2C+%223600s"
                "%22%2C+%22avg%22%29%2C+%22some.target%22%29"
                "&target=alias%28summarize%28some.other.target"
                "%2C+%223600s%22%2C+%22avg%22%29%2C+%22"
                "some.other.target%22%29&format=json")
            self.assertEqual(
                result,
                [{'metadata': {'some-field': 'lorem'},
                  'datapoints': self.M1_PROCESSED_DATAPOINTS},
                 {'metadata': {'some-field': 'ipsum'},
                  'datapoints': self.M2_PROCESSED_DATAPOINTS}])
        deferredResult.addCallback(assert_handle_render_request)

        deferredResult.callback(None)
        return deferredResult

    def test_get_data_for_kwargs(self):
        m1 = mk_graphite_metric(
            target='some.target',
            metadata={'some-field': 'lorem'})
        m2 = mk_graphite_metric(
            target='some.other.target',
            metadata={'some-field': 'ipsum'})

        response_data = json.dumps([
            {"target": "some.target",
             "datapoints": self.M1_RAW_DATAPOINTS},
            {"target": "some.other.target",
             "datapoints": self.M2_RAW_DATAPOINTS}])
        self.stub_getPage(response_data)

        backend = self.mk_graphite_backend(
            graphite_url='http://some-graphite-url.moc:8080/',
            from_time=3600,
            metrics=[m1, m2])
        deferredResult = backend.get_data(
            graphite_url='http://some-new-graphite-url.moc:7112/',
            from_time='2h')

        def assert_handle_render_request(result):
            client.getPage.assert_called_with(
                "http://some-new-graphite-url.moc:7112/render/?from=-7200s"
                "&target=alias%28summarize%28some.target%2C+%223600s"
                "%22%2C+%22avg%22%29%2C+%22some.target%22%29"
                "&target=alias%28summarize%28some.other.target"
                "%2C+%223600s%22%2C+%22avg%22%29%2C+%22"
                "some.other.target%22%29&format=json")
            self.assertEqual(
                result,
                [{'metadata': {'some-field': 'lorem'},
                  'datapoints': self.M1_PROCESSED_DATAPOINTS},
                 {'metadata': {'some-field': 'ipsum'},
                  'datapoints': self.M2_PROCESSED_DATAPOINTS}])
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

    def test_parse_config(self):
        config = {
            'target': 'some.target',
            'bucket_size': '1h',
            'null_filter': 'zeroize',
            'metadata': {'name': 'luke-the-metric'}
        }
        class_defaults = {'SomeType': "some default value"}

        new_config = GraphiteMetric.parse_config(config, class_defaults)
        self.assertEqual(new_config, {
            'target': 'some.target',
            'bucket_size': 3600,
            'null_filter': 'zeroize',
            'wrapped_target': ('alias(summarize(some.target, "3600s", "avg"), '
                               '"some.target")'),
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
        metric = mk_graphite_metric(null_filter='zeroize')

        expected_processed_datapoints = [
            {'x': 1342382400, 'y': 0},
            {'x': 1342386000, 'y': 0.04924959844054583},
            {'x': 1342389600, 'y': 0.05052084873949578}]
        processed_datapoints = metric.process_datapoints(datapoints)
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
