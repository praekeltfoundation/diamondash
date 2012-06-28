"""Tests for diamondash's server side"""

import json
from diamondash import server
from diamondash.dashboard import Dashboard
from pkg_resources import resource_stream
from twisted.trial import unittest
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import Protocol, Factory


class MockGraphiteServerProtocol(Protocol):
    """A protocol for MockGraphiteServerMixin"""

    def dataReceived(self, data):
        response = self.handle_request(data)
        self.transport.write(response.encode('utf-8'))
        self.transport.loseConnection()

    def get_request_uri(self, data):
        return data.split(' ')[1]

    def construct_response(self, request_uri):
        response_data = self.factory.test_data.get(request_uri)
        response = ["HTTP/1.1 %s" % (response_data['code'],)]
        response.extend(['', json.dumps(response_data['body'])])
        return '\r\n'.join(response)

    def handle_request(self, data):
        request_uri = self.get_request_uri(data)
        response = self.construct_response(request_uri)
        return response


class MockGraphiteServerMixin(object):
    """
    A mock Graphite server mixin, providing metric data from captured
    Graphite response data
    """

    @inlineCallbacks
    def start_graphite_ws(self, test_data):
        factory = Factory()
        factory.protocol = MockGraphiteServerProtocol
        factory.test_data = test_data
        self.graphite_ws = yield reactor.listenTCP(0, factory)
        address = self.graphite_ws.getHost()
        self.graphite_url = "http://%s:%s" % (address.host, address.port)

    def stop_graphite_ws(self):
        return self.graphite_ws.loseConnection()


class DiamondashServerGraphiteTestCase(unittest.TestCase,
                                       MockGraphiteServerMixin):
    """Tests the diamondash web server's communication with graphite"""

    _TEST_DATA = json.load(
        resource_stream(__name__, 'graphite_test_data.json'))

    @inlineCallbacks
    def setUp(self):
        yield self.start_graphite_ws(self._TEST_DATA)

        test_dashboard_name = 'test-dashboard'
        test_widget_config = {
            'random-count-sum': {
                'type': 'graph',
                'metric': 'vumi.random.count.sum',
            },
        }

        # initialise the server configuration
        server.server_config = server.ServerConfig(
            graphite_url=self.graphite_url)

        # add a test dashboard
        server.add_dashboard(Dashboard(
            name=test_dashboard_name,
            widget_config=test_widget_config))

    def tearDown(self):
        self.stop_graphite_ws()

    # TODO render tests for other widget types

    def assert_response(self, response_data, expected_response):
        """
        Asserts whether the response obtained matches
        the expected response
        """
        response = json.loads(response_data)
        self.assertEqual(response, expected_response)

    def test_get_render_results_for_graph(self):
        """Tests whether graphite render results are obtained properly"""
        # TODO
        render_uri = '/render/?target=vumi.random.count.sum' + \
            '&from=-5minutes' + \
            '&format=json'
        render_url = self.graphite_url + render_uri
        expected_response = self._TEST_DATA[render_uri]['body']
        d = server.get_render_results(render_url)
        d.addCallback(self.assert_response, expected_response)
        return d


class DiamondashServerClientTestCase(unittest.TestCase):
    """
    Tests the diamondash web server's response logic for client side
    requests (eg. url construction and data formatting)
    """

    _TEST_DATA = json.load(
        resource_stream(__name__, 'client_test_data.json'))

    """
    Url construction tests
    ----------------------
    """

    # TODO url construction tests for other widget types

    def test_construct_render_url_for_graph(self):
        """
        Tests whether graphite render request urls are constructed
        properly from client side render requests
        """
        test_dashboard_name = 'test-dashboard'
        test_widget_config = {
            'random-count-sum': {
                'type': 'graph',
                'metric': 'vumi.random.count.sum',
            },
        }

        # initialise the server configuration
        server.server_config = server.ServerConfig(
            graphite_url="http://127.0.0.1:8000",
            render_time_span=5)

        # add a test dashboard
        server.add_dashboard(Dashboard(
            name=test_dashboard_name,
            widget_config=test_widget_config))

        client_request_uri = '/render/test-dashboard/random-count-sum'

        correct_render_url = 'http://127.0.0.1:8000' + \
            '/render/?target=vumi.random.count.sum&from=-' + \
            '5minutes&format=json'

        constructed_render_url = \
            server.construct_render_url('test-dashboard', 'random-count-sum')
        self.assertEqual(constructed_render_url, correct_render_url)

    """
    Purification tests
    ------------------
    """
    def test_purify_render_results_nulls(self):
        """
        Tests whether null values in graphite render results are
        handled appropriately
        """
        before = self._TEST_DATA['test_purify_render_results_nulls']['before']
        after = self._TEST_DATA['test_purify_render_results_nulls']['after']
        purified = server.purify_render_results(before)
        self.assertEqual(purified, after)

    """
    Formatting tests
    ----------------
    """

    # TODO formatting tests for other widget types

    def test_format_render_results_for_graph(self):
        """
        Tests whether graphite render results are formatted
        as expected by the client side for graph widgets
        """
        before = self._TEST_DATA['test_format_render_results_for_graph']['before']
        after = self._TEST_DATA['test_format_render_results_for_graph']['after']
        formatted = server.format_render_results(before)
        self.assertEqual(formatted, after)
