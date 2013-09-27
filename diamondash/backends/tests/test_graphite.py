import json
import time
from urlparse import urlsplit, parse_qs

from twisted.internet.defer import Deferred
from twisted.web import client
from twisted.trial import unittest

from diamondash.tests.utils import stub_from_config
from diamondash import utils, ConfigError

from diamondash.backends import processors
from diamondash.backends.processors import (
    AggregatingSummarizer,
    LastDatapointSummarizer)

from diamondash.backends.graphite import (
    GraphiteBackend, GraphiteMetric, guess_aggregation_method)


def mk_graphite_metric(target='some.target.max', **kwargs):
    kwargs = utils.update_dict({
        'metadata': {},
        'target': target,
        'null_filter': processors.null_filters['zeroize'],
    }, kwargs)
    return GraphiteMetric(**kwargs)


class GraphiteBackendTestCase(unittest.TestCase):
    TIME = 10800  # 3 hours since the unix epoch
    FROM_TIME = -7200  # 2 hours from 'now'
    UNTIL_TIME = -3600  # 1 hour from 'now'
    BUCKET_SIZE = 300  # 5 minutes

    M1_TARGET = 'some.target.max'
    M1_METADATA = {'some-field': 'lorem'}
    M1_RAW_DATAPOINTS = [
        [None, 3773],
        [5.0, 5695],
        [10.0, 5700],
        [12.0, 7114]]
    M1_PROCESSED_DATAPOINTS = [
        {'x': 3600, 'y': 0},
        {'x': 5700, 'y': 10.0},
        {'x': 7200, 'y': 12.0}]

    M2_TARGET = 'some.other.target.sum'
    M2_METADATA = {'some-field': 'ipsum'}
    M2_RAW_DATAPOINTS = [
        [12.0, 3724],
        [14.0, 3741],
        [25.0, 4638],
        [None, 4829],
        [11.0, 6075]]
    M2_PROCESSED_DATAPOINTS = [
        {'x': 3600, 'y': 26.0},
        {'x': 4500, 'y': 25.0},
        {'x': 6000, 'y': 11.0}]

    RESPONSE_DATA = json.dumps([
        {"target": M1_TARGET, "datapoints": M1_RAW_DATAPOINTS},
        {"target": M2_TARGET, "datapoints": M2_RAW_DATAPOINTS}])

    def setUp(self):
        self.m1 = mk_graphite_metric(
            target=self.M1_TARGET,
            metadata=self.M1_METADATA,
            null_filter=processors.null_filters['zeroize'],
            summarizer=processors.summarizers.get(
                'last',
                'round',
                self.BUCKET_SIZE))

        self.m2 = mk_graphite_metric(
            target=self.M2_TARGET,
            metadata=self.M2_METADATA,
            null_filter=processors.null_filters['skip'],
            summarizer=processors.summarizers.get(
                'sum',
                'round',
                self.BUCKET_SIZE))

        self.backend = GraphiteBackend(
            graphite_url='http://some-graphite-url.moc:8080',
            metrics=[self.m1, self.m2])
        self.last_request_url = None
        self.stub_time(self.TIME)
        self.stub_getPage()

    def stub_getPage(self):
        d = Deferred()
        d.addCallback(lambda _: self.RESPONSE_DATA)

        def stubbed_getPage(url):
            self.last_requested_url = url
            return d
        self.patch(client, 'getPage', stubbed_getPage)

    def stub_time(self, t):
        self.patch(time, 'time', lambda: t)

    def assert_url(self, url, expected_base, expected_path, **expected_params):
        url_parts = urlsplit(url)
        self.assertEqual(expected_params, parse_qs(url_parts.query))
        self.assertEqual(expected_base, "http://%s" % url_parts.netloc)
        self.assertEqual(expected_path, url_parts.path)

    def assert_request_url(self, url, expected_url_params):
        expected_url_params.update({
            'format': ['json'],
            'target': [self.m1.wrapped_target, self.m2.wrapped_target],
        })
        self.assert_url(url, self.backend.graphite_url, '/render/',
                        **expected_url_params)

    def test_parse_config(self):
        stub_from_config(GraphiteMetric)
        config = {
            'null_filter': 'zeroize',
            'bucket_size': 3600,
            'time_aligner': 'round',
            'graphite_url': 'http://some-graphite-url.moc:8080/',
            'metrics': [
                {'target': 'a.max'},
                {'target': 'b.max', 'null_filter': 'skip'}]
        }
        class_defaults = {'SomeType': "some default value"}

        parsed_config = GraphiteBackend.parse_config(config, class_defaults)
        self.assertEqual(parsed_config, {
            'graphite_url': 'http://some-graphite-url.moc:8080/',
            'metrics': [
                ({
                    'target': 'a.max',
                    'bucket_size': 3600,
                    'time_aligner': 'round',
                    'null_filter': 'zeroize'
                }, class_defaults),
                ({
                    'target': 'b.max',
                    'bucket_size': 3600,
                    'time_aligner': 'round',
                    'null_filter': 'skip'
                }, class_defaults)
            ]
        })

    def test_parse_config_for_no_graphite_url(self):
        self.assertRaises(ConfigError, GraphiteBackend.parse_config, {})

    def test_request_url_building(self):
        self.assert_request_url(self.backend.build_request_url(
            **{'from_time': '3600'}),
            {'from': ['3600']})

        self.assert_request_url(self.backend.build_request_url(
            **{'until_time': '3600'}),
            {'until': ['3600']})

        self.assert_request_url(self.backend.build_request_url(
            **{'from_time': '7200', 'until_time': '3600'}),
            {'from': ['7200'], 'until': ['3600']})

    def test_data_retrieval(self):
        deferred_result = self.backend.get_data(
            from_time=self.FROM_TIME,
            until_time=self.UNTIL_TIME)

        def assert_retrieved_data(result):
            self.assert_request_url(
                self.last_requested_url,
                {'from': ['3600'], 'until': ['7200']})

            self.assertEqual(
                result,
                [{'metadata': self.M1_METADATA,
                  'datapoints': self.M1_PROCESSED_DATAPOINTS},
                 {'metadata': self.M2_METADATA,
                  'datapoints': self.M2_PROCESSED_DATAPOINTS}])
        deferred_result.addCallback(assert_retrieved_data)

        deferred_result.callback(None)
        return deferred_result


class GraphiteMetricTestCase(unittest.TestCase):
    def test_parse_config(self):
        config = {
            'target': 'some.target.max',
            'bucket_size': '1h',
            'null_filter': 'zeroize',
            'metadata': {'name': 'luke-the-metric'}
        }

        new_config = GraphiteMetric.parse_config(config)
        self.assertEqual(new_config['target'], config['target'])
        self.assertEqual(new_config['metadata'], {'name': 'luke-the-metric'})
        self.assertEqual(
            new_config['null_filter'],
            processors.null_filters['zeroize'])
        self.assertEqual(
            set(new_config.keys()),
            set(['target', 'metadata', 'null_filter', 'summarizer']))

    def test_parse_config_for_no_bucket_size(self):
        config = GraphiteMetric.parse_config({'target': 'some.random.target'})
        self.assertTrue('summarizer' not in config)

    def test_parse_config_for_summarizer(self):
        def assert_agg_summarizer(config, bucket_size, agg_name):
            summarizer = GraphiteMetric.parse_config(config)['summarizer']
            self.assertTrue(isinstance(summarizer, AggregatingSummarizer))
            self.assertEqual(summarizer.aggregator,
                             processors.aggregators[agg_name])
            self.assertEqual(summarizer.bucket_size, bucket_size)

        def assert_ldp_summarizer(config, bucket_size):
            summarizer = GraphiteMetric.parse_config(config)['summarizer']
            self.assertEqual(summarizer.bucket_size, bucket_size)
            self.assertTrue(isinstance(summarizer, LastDatapointSummarizer))

        assert_agg_summarizer(
            {'target': 'some.target.avg', 'bucket_size': '1h'}, 3600, 'avg')
        assert_agg_summarizer(
            {'target': 'some.target.sum', 'bucket_size': '2h'}, 7200, 'sum')
        assert_agg_summarizer(
            {'target': 'some.target.min', 'bucket_size': '1h'}, 3600, 'min')
        assert_agg_summarizer(
            {'target': 'some.target.max', 'bucket_size': '2h'}, 7200, 'max')

        assert_ldp_summarizer(
            {'target': 'some.target.last', 'bucket_size': '2h'}, 7200)

    def test_parse_config_for_no_target(self):
        self.assertRaises(ConfigError, GraphiteMetric.parse_config, {})

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
