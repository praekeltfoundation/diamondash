"""Tests for diamondash's server side"""

import json
from pkg_resources import resource_stream

from klein.test_resource import requestMock
from twisted.trial import unittest
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import Protocol, Factory

from diamondash import server
from diamondash.server import DASHBOARD_DEFAULTS, DiamondashServer

from diamondash.dashboard import Dashboard


class MockGraphiteServerProtocol(Protocol):
    """A protocol for MockGraphiteServerMixin"""

    def dataReceived(self, data):
        response = self.handle_request(data)
        self.transport.write(response.encode('utf-8'))
        self.transport.loseConnection()

    def get_request_uri(self, data):
        return data.split(' ')[1]

    def build_response(self, request_uri):
        response_data = self.factory.response_data.get(request_uri)

        if response_data is None:
            response = ['HTTP/1.1 404', '', '']
        else:
            response = ['HTTP/1.1 %s' % (response_data['code'],)]
            response.extend(['', json.dumps(response_data['body'])])

        return '\r\n'.join(response)

    def handle_request(self, data):
        request_uri = self.get_request_uri(data)
        response = self.build_response(request_uri)
        return response


class MockGraphiteServerMixin(object):
    """
    A mock Graphite server mixin, providing metric data from captured
    Graphite response data
    """

    RESPONSE_DATA = json.load(resource_stream(__name__, 'response_data.json'))

    graphite_ws = None

    @inlineCallbacks
    def start_graphite_ws(self):
        factory = Factory()
        factory.protocol = MockGraphiteServerProtocol
        factory.response_data = self.RESPONSE_DATA
        self.graphite_ws = yield reactor.listenTCP(0, factory)
        address = self.graphite_ws.getHost()
        self.graphite_url = "http://%s:%s" % (address.host, address.port)

    def stop_graphite_ws(self):
        return self.graphite_ws.loseConnection()


class MockDashboard:
    """A mock for the Dashboard class"""

    def __init__(self, config):
        self.is_mock = True
        self.config = config

    def get_widget_config(self, widget_name):
        return None


class DiamondashServerTestCase(unittest.TestCase):

    def test_add_dashboard(self):
        """
        Should add a dashboard to the server's dashboard list, as well as the
        server's name-dashboard and share_id-dashboard lookups.
        """
        dashboard_config = {
            'name': 'lorem',
            'share_id': 'ipsum'
        }
        mock_dashboard = MockDashboard(dashboard_config)

        dd_server = DiamondashServer('', [])
        dd_server.add_dashboard(mock_dashboard)

        self.assertTrue(dd_server.dashboards[0].is_mock)
        self.assertTrue(dd_server.dashboards_by_name['lorem'].is_mock)
        self.assertTrue(dd_server.dashboards_by_share_id['ipsum'].is_mock)


class WebServerTestCase(unittest.TestCase, MockGraphiteServerMixin):

    TEST_DATA = json.load(
        resource_stream(__name__, 'test_server_data/server_test_data.json'))

    def setUp(self):
        self.graphite_ws = None

    def tearDown(self):
        if self.graphite_ws:
            self.stop_graphite_ws()

    def configure_server(self, dashboard_configs):
        """
        Configures the diamondash server with a single dashboard
        """
        dashboards = [Dashboard(d_config) for d_config in dashboard_configs]
        server.server = DiamondashServer(self.graphite_url, dashboards)

    def mock_request(self, input):
        host = self.graphite_ws.getHost()
        return requestMock(input, host=host.host, port=host.port)

    def assert_response(self, response_data, expected_response):
        """
        Asserts whether the response obtained matches
        the expected response
        """
        response = json.loads(response_data)
        self.assertEqual(response, expected_response)

    """
    Render tests
    ------------
    """
    def test_render_for_nonexistent_dashboard(self):
        """
        Should return an empty json object as a response if the dashboard does
        not exist
        """
        server.server = DiamondashServer('http://someurl.com/', [])
        response = server.render(None, 'test-dashboard', 'some_metric')
        self.assertEqual(response, "{}")

    def test_render_for_nonexistent_widget(self):
        """
        Should return an empty json object as a response if the dashboard does
        not exist
        """
        dashboard = MockDashboard({'name': 'test-dashboard'})
        server.server = DiamondashServer('http://someurl.com/', [dashboard])
        response = server.render(None, 'test-dashboard', 'some_metric')
        self.assertEqual(response, "{}")

    @inlineCallbacks
    def test_render_for_graph(self):
        """
        Should send a request to graphite, apply transformations,
        and return data useable by the client side for graph widgets
        """
        yield self.start_graphite_ws()

        dashboard_config = dict(DASHBOARD_DEFAULTS, **{
            'name': 'test-dashboard',
            'widgets': [
                {
                    'name': 'random-count-sum',
                    'time_range': 3600,
                    'title': 'a graph',
                    'type': 'graph',
                    'bucket_size': 300,
                    'metrics': {
                        'luke the metric': {
                            'target': 'vumi.random.count.sum'
                        }
                    },
                }
            ],
        })
        self.configure_server([dashboard_config])

        test_data_key = 'test_render_for_graph'
        input = self.TEST_DATA[test_data_key]['input']
        output = self.TEST_DATA[test_data_key]['output']

        request = self.mock_request(input)
        d = server.render(request, 'test-dashboard', 'random-count-sum')
        d.addCallback(self.assert_response, output)
        yield d

    @inlineCallbacks
    def test_render_for_multimetric_graph(self):
        """
        Should send a request to graphite, apply transformations,
        and return data useable by the client side for graph widgets
        """
        yield self.start_graphite_ws()

        dashboard_config = dict(DASHBOARD_DEFAULTS, **{
            'name': 'test-dashboard',
            'widgets': [
                {
                    'name': 'random-count-sum-and-average',
                    'time_range': 3600,
                    'title': 'a graph',
                    'type': 'graph',
                    'bucket_size': 300,
                    'metrics': {
                        'random-count-sum': {
                            'target': 'vumi.random.count.sum'
                        },
                        'random-timer-average': {
                            'target': 'vumi.random.timer.avg'
                        }
                    },
                }
            ]
        })
        self.configure_server([dashboard_config])

        test_data_key = 'test_render_for_multimetric_graph'
        input = self.TEST_DATA[test_data_key]['input']
        output = self.TEST_DATA[test_data_key]['output']

        request = self.mock_request(input)
        d = server.render(request, 'test-dashboard',
                          'random-count-sum-and-average')
        d.addCallback(self.assert_response, output)
        yield d

    @inlineCallbacks
    def test_render_for_lvalue(self):
        """
        Should send a request to graphite, apply transformations,
        and return data useable by the client side for lvalue widgets
        """
        yield self.start_graphite_ws()

        dashboard_config = dict(DASHBOARD_DEFAULTS, **{
            'name': 'test-dashboard',
            'widgets': [
                {
                    'name': 'some-lvalue-widget',
                    'time_range': '1d',
                    'type': 'lvalue',
                    'metrics': ['vumi.random.count.sum'],
                }
            ],
        })
        self.configure_server([dashboard_config])

        test_data_key = 'test_render_for_lvalue'
        input = self.TEST_DATA[test_data_key]['input']
        output = self.TEST_DATA[test_data_key]['output']

        request = self.mock_request(input)
        d = server.render(request, 'test-dashboard', 'some-lvalue-widget')
        d.addCallback(self.assert_response, output)
        yield d

    @inlineCallbacks
    def test_render_for_multimetric_lvalue(self):
        """
        Should send a request to graphite, apply transformations,
        and return data useable by the client side for lvalue widgets
        """
        yield self.start_graphite_ws()

        dashboard_config = dict(DASHBOARD_DEFAULTS, **{
            'name': 'test-dashboard',
            'widgets': [
                {
                    'name': 'some-multimetric-lvalue-widget',
                    'time_range': '1h',
                    'type': 'lvalue',
                    'metrics': ['vumi.random.count.sum',
                                'vumi.random.timer.sum'],
                },
            ]
        })

        self.configure_server([dashboard_config])

        test_data_key = 'test_render_for_multimetric_lvalue'
        input = self.TEST_DATA[test_data_key]['input']
        output = self.TEST_DATA[test_data_key]['output']

        request = self.mock_request(input)
        d = server.render(request, 'test-dashboard',
                          'some-multimetric-lvalue-widget')
        d.addCallback(self.assert_response, output)
        yield d

    """
    Purification tests
    ------------------
    """
    def test_skip_nulls(self):
        """
        Should return datapoints without null values by
        skipping coordinates withh null x or y values
        """
        test_data_key = 'test_skip_nulls'
        before = self.TEST_DATA[test_data_key]['before']
        after = self.TEST_DATA[test_data_key]['after']
        purified = server.skip_nulls(before)
        self.assertEqual(purified, after)

    def test_zeroize_nulls(self):
        """
        Should return datapoints without null values by
        skipping coordinates with null x or y values
        """
        test_data_key = 'test_zeroize_nulls'
        before = self.TEST_DATA[test_data_key]['before']
        after = self.TEST_DATA[test_data_key]['after']
        purified = server.zeroize_nulls(before)
        self.assertEqual(purified, after)

    """
    Formatting tests
    ----------------
    """

    def test_format_results_for_graph(self):
        """
        Should format datapoints in graphite's format to
        datapoints in rickshaw's format
        """

        widget_config = {
            'title': 'a graph',
            'type': 'graph',
            'metrics': {
                'arnold-the-metric': {
                    'target': 'vumi.random.count.sum'
                }
            },
        }

        test_data_key = 'test_format_results_for_graph'
        before = self.TEST_DATA[test_data_key]['before']
        after = self.TEST_DATA[test_data_key]['after']
        formatted = server.format_results_for_graph(before, widget_config)
        formatted_str = json.loads(formatted)
        self.assertEqual(formatted_str, after)

    def test_format_results_for_multimetric_graph(self):
        """
        Should format datapoints in graphite's format to
        datapoints in rickshaw's format
        """
        widget_config = {
            'title': 'a graph',
            'type': 'graph',
            'metrics': {
                'random-count-sum': {
                    'target': 'vumi.random.count.sum'
                },
                'random-timer-average': {
                    'target': 'vumi.random.timer.avg'
                }
            },
        }

        test_data_key = 'test_format_results_for_multimetric_graph'
        before = self.TEST_DATA[test_data_key]['before']
        after = self.TEST_DATA[test_data_key]['after']
        formatted = server.format_results_for_graph(before, widget_config)
        formatted_str = json.loads(formatted)
        self.assertEqual(formatted_str, after)

    def test_format_results_for_lvalue(self):
        """
        Should format datapoints in graphite's format to
        datapoints in a format useable for lvalue widgets
        """
        def assert_format(data, config, expected):
            result = server.format_results_for_lvalue(data, config)
            self.assertEqual(result, expected)

        data = (3.034992, 2.0, 1341318035)
        config = {'time_range': 86400}
        expected = ('{"lvalue": "2", "percentage": "-34%", '
                    '"from": "2012-07-03 12:20, "diff": -1.035, '
                    '"to": "2012-07-03 12:20"}')
        expected = ('{"lvalue": "2", "percentage": "-34%", '
                    '"from": "2012-07-03 12:20", "diff": "-1.035", '
                    '"to": "2012-07-04 12:20"}')
        assert_format(data, config, expected)

        data = (0, 0, 1341318035)
        config = {'time_range': 86400}
        expected = ('{"lvalue": "0", "percentage": "0%", '
                    '"from": "2012-07-03 12:20", "diff": "0", '
                    '"to": "2012-07-04 12:20"}')
        assert_format(data, config, expected)

    """
    Other tests
    ------------
    """

    def test_aggregate_results_for_lvalue(self):
        """
        Should obtain a tuple consisting of three aggregates accross
        multiple datapoint lists:
            - the summed previous y value
            - the summed last y value
            - the maximum last x value (latest time)
        """
        def assert_aggregation(data, expected):
            result = server.aggregate_results_for_lvalue(data)
            self.assertEqual(result, expected)

        data = [[[4, 200],
                 [-5, 300]],
                [[3, -1],
                 [2, 301]]]
        expected = (7, -3, 301)
        assert_aggregation(data, expected)

        data = [[[1.0, 1341318015],
                 [3.0, 1341318020],
                 [3.0, 1341318025],
                 [2.0, 1341318030]],
                [[0.060949, 1341318025],
                 [0.045992, 1341318030],
                 [None, 1341318035]]]
        expected = (3.045992, 2.0, 1341318035)
        assert_aggregation(data, expected)

    def test_get_result_datapoints(self):
        """
        Should obtain a list of datapoint lists, each list
        corresponding to a metric
        """
        test_data_key = 'test_get_result_datapoints'
        before = self.TEST_DATA[test_data_key]['before']
        before_str = json.dumps(before)
        result = server.get_result_datapoints(before_str)
        after = self.TEST_DATA[test_data_key]['after']
        self.assertEqual(result, after)

    def test_format_value(self):
        def assert_format(input, expected):
            result = server.format_value(input)
            self.assertEqual(result, expected)

        assert_format(999999, '999.999K')
        assert_format(1999999, '2.000M')
        assert_format(1234123456789, '1.234T')
        assert_format(123456123456789, '123.456T')
        assert_format(3.034992, '3.035')
        assert_format(2, '2')
        assert_format(2.0, '2')

    def test_format_time(self):
        def assert_format(input, expected):
            result = server.format_time(input)
            self.assertEqual(result, expected)

        assert_format(1341318035, '2012-07-03 12:20')
        assert_format(1841318020, '2028-05-07 13:13')
