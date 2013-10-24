import json
import time
from itertools import count
from urlparse import urlsplit, parse_qs

from twisted.internet.defer import Deferred
from twisted.web import client
from twisted.trial import unittest

from diamondash import utils
from diamondash.config import ConfigError

from diamondash.backends import base as backends
from diamondash.backends.graphite import (
    GraphiteBackendConfig, GraphiteBackend, GraphiteMetricConfig,
    guess_aggregation_method)


def mk_metric_config_data(**overrides):
    return utils.add_dicts({
        'target': 'a.last',
        'bucket_size': '1h',
        'null_filter': 'zeroize',
        'metadata': {'name': 'max of a'}
    }, overrides)


def mk_backend_config_data(**overrides):
    return utils.add_dicts({
        'null_filter': 'zeroize',
        'bucket_size': '5m',
        'time_aligner': 'round',
        'url': 'http://some-graphite-url.moc:8080/',
        'metrics': [{
            'target': 'a.last',
            'null_filter': 'zeroize',
            'metadata': {'name': 'max of a'}
        }, {
            'target': 'b.sum',
            'null_filter': 'skip',
            'metadata': {'name': 'sum of b'}
        }]
    }, overrides)


class GraphiteBackendConfigTestCase(unittest.TestCase):
    def test_parsing(self):
        config = GraphiteBackendConfig(mk_backend_config_data())

        m1_config, m2_config = config['metrics']
        self.assertEqual(m1_config['target'], 'a.last')
        self.assertEqual(m1_config['bucket_size'], 300000)
        self.assertEqual(m1_config['time_aligner'], 'round')
        self.assertEqual(m1_config['null_filter'], 'zeroize')

        self.assertEqual(m2_config['target'], 'b.sum')
        self.assertEqual(m2_config['bucket_size'], 300000)
        self.assertEqual(m2_config['time_aligner'], 'round')
        self.assertEqual(m2_config['null_filter'], 'skip')

    def test_parsing_for_no_url(self):
        config = mk_backend_config_data()
        del config['url']

        self.assertRaises(ConfigError, GraphiteBackendConfig.parse, config)


class GraphiteBackendTestCase(unittest.TestCase):
    TIME = 10800  # 3 hours since the unix epoch

    FROM_TIME = -7200000  # 2 hours from 'now'
    UNTIL_TIME = -3600000  # 1 hour from 'now'

    M1_RAW_DATAPOINTS = [
        [None, 3773],
        [5.0, 5695],
        [10.0, 5700],
        [12.0, 7114]]
    M1_PROCESSED_DATAPOINTS = [
        {'x': 3600000, 'y': 0},
        {'x': 5700000, 'y': 10.0},
        {'x': 7200000, 'y': 12.0}]

    M2_RAW_DATAPOINTS = [
        [12.0, 3724],
        [14.0, 3741],
        [25.0, 4638],
        [None, 4829],
        [11.0, 6075]]
    M2_PROCESSED_DATAPOINTS = [
        {'x': 3600000, 'y': 26.0},
        {'x': 4500000, 'y': 25.0},
        {'x': 6000000, 'y': 11.0}]

    RESPONSE_DATA = json.dumps([
        {'target': 'a.last', 'datapoints': M1_RAW_DATAPOINTS},
        {'target': 'b.sum', 'datapoints': M2_RAW_DATAPOINTS}])

    def setUp(self):
        self.uuid_counter = count()
        self.patch(backends, 'uuid4', lambda: next(self.uuid_counter))

        config = GraphiteBackendConfig(mk_backend_config_data())
        self.backend = GraphiteBackend(config)

        self.m1, self.m2 = self.backend.metrics

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
        self.assertEqual(expected_base, "http://%s/" % url_parts.netloc)
        self.assertEqual(expected_path, url_parts.path)

    def assert_request_url(self, url, expected_url_params):
        expected_url_params.update({
            'format': ['json'],
            'target': [
                self.m1.aliased_target(),
                self.m2.aliased_target()],
        })

        self.assert_url(
            url,
            self.backend.config['url'],
            '/render/',
            **expected_url_params)

    def test_request_url_building(self):
        self.assert_request_url(self.backend.build_request_url(
            **{'from_time': 3600000}),
            {'from': ['3600']})

        self.assert_request_url(self.backend.build_request_url(
            **{'until_time': 3600000}),
            {'until': ['3600']})

        self.assert_request_url(self.backend.build_request_url(
            **{'from_time': 7200000, 'until_time': 3600000}),
            {'from': ['7200'], 'until': ['3600']})

    def test_data_retrieval(self):
        deferred_result = self.backend.get_data(
            from_time=self.FROM_TIME,
            until_time=self.UNTIL_TIME)

        def assert_retrieved_data(result):
            self.assert_request_url(
                self.last_requested_url,
                {'from': ['3600'], 'until': ['7200']})

            self.assertEqual(result, [{
                'id': '0',
                'datapoints': self.M1_PROCESSED_DATAPOINTS
            }, {
                'id': '1',
                'datapoints': self.M2_PROCESSED_DATAPOINTS
            }])

        deferred_result.addCallback(assert_retrieved_data)
        deferred_result.callback(None)
        return deferred_result


class GraphiteMetricConfigTestCase(unittest.TestCase):
    def test_parsing(self):
        config = GraphiteMetricConfig(mk_metric_config_data())
        self.assertEqual(config['bucket_size'], 3600000)
        self.assertEqual(config['metadata'], {'name': 'max of a'})


class GraphiteMetricTestCase(unittest.TestCase):
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
