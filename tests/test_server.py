"""Tests for diamondash's server side"""

import json
from urllib import urlencode
from pkg_resources import resource_stream
from klein.test_resource import requestMock
from diamondash import server
from diamondash.dashboard import Dashboard
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
        response_data = self.factory.response_data.get(request_uri)
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

    _RESPONSE_DATA = json.load(
        resource_stream(__name__, 'response_data.json'))

    graphite_ws = None

    @inlineCallbacks
    def start_graphite_ws(self):
        factory = Factory()
        factory.protocol = MockGraphiteServerProtocol
        factory.response_data = self._RESPONSE_DATA
        self.graphite_ws = yield reactor.listenTCP(0, factory)
        address = self.graphite_ws.getHost()
        self.graphite_url = "http://%s:%s" % (address.host, address.port)

    def stop_graphite_ws(self):
        return self.graphite_ws.loseConnection()


class DiamondashServerTestCase(unittest.TestCase, MockGraphiteServerMixin):

    _TEST_DATA = json.load(
        resource_stream(__name__, 'server_test_data.json'))

    def setUp(self):
        self.graphite_ws = None

    def tearDown(self):
        if self.graphite_ws:
            self.stop_graphite_ws()

    # TODO render tests for other widget types

    def assert_response(self, response_data, expected_response):
        """
        Asserts whether the response obtained matches
        the expected response
        """
        response = json.loads(response_data)
        self.assertEqual(response, expected_response)

    @inlineCallbacks
    def test_render_for_graph(self):
        """
        Should build a graphite url from the passed in client
        request, send a request to graphite, apply transformations, 
        and return data useable by the client side
        """
        yield self.start_graphite_ws()

        test_render_time_span = 5

        # initialise the server configuration
        server.config = server.ServerConfig(
            graphite_url=self.graphite_url,
            render_time_span=test_render_time_span)

        config = {
        'name': 'test-dashboard',
        'widgets': {
                'random-count-sum': {
                    'title': 'a graph',
                    'type': 'graph',
                    'metric': 'vumi.random.count.sum'
                }
            }
        }
        server.add_dashboard(Dashboard(config))

        input = self._TEST_DATA['test_render_for_graph']['input']
        request = requestMock(input, host=self.graphite_ws.getHost().host,
                              port=self.graphite_ws.getHost().port)
        output = self._TEST_DATA['test_render_for_graph']['output']
        d = server.render(request, 'test-dashboard', 'random-count-sum')
        d.addCallback(self.assert_response, output)
        yield d

    """
    Url construction tests
    ----------------------
    """

    # TODO url construction tests widget or dashboard not found
    # TODO url construction tests for other widget types

    def test_construct_render_url_for_graph(self):
        """
        Should construct render request urls acceptable to graphite
        from a client side graph render request
        """
        # initialise the server configuration
        test_graphite_url = "http://127.0.0.1:8000"
        test_render_time_span = 5
        server.config = server.ServerConfig(
            graphite_url=test_graphite_url,
            render_time_span=test_render_time_span)

        config = {
        'name': 'test-dashboard',
        'widgets': {
                'random-count-sum': {
                    'title': 'a graph',
                    'type': 'graph',
                    'metric': 'vumi.random.count.sum'
                }
            }
        }
        server.add_dashboard(Dashboard(config))

        params = {
            'target': 'vumi.random.count.sum',
            'from': '-%sminutes' % (test_render_time_span,),
            'format': 'json'
            }
        correct_render_url = "%s/render/?%s" % (test_graphite_url,
                                                urlencode(params))

        constructed_render_url = server.construct_render_url(
            'test-dashboard', 
            'random-count-sum')
        self.assertEqual(constructed_render_url, correct_render_url)

    """
    Purification tests
    ------------------
    """
    def test_skip_nulls(self):
        """
        Should return datapoints without null values by
        skipping coordinates withh null x or y values
        """
        before = self._TEST_DATA['test_skip_nulls']['before']
        after = self._TEST_DATA['test_skip_nulls']['after']
        purified = server.skip_nulls(before)
        self.assertEqual(purified, after)

    def test_zeroize_nulls(self):
        """
        Should return datapoints without null values by
        skipping coordinates with null x or y values
        """
        before = self._TEST_DATA['test_zeroize_nulls']['before']
        after = self._TEST_DATA['test_zeroize_nulls']['after']
        purified = server.zeroize_nulls(before)
        self.assertEqual(purified, after)

    """
    Formatting tests
    ----------------
    """

    # TODO formatting tests for other widget types

    def test_format_render_results_for_graph(self):
        """
        Should format datapoints in graphite's format to 
        datapoints in rickshaw's format
        """
        before = self._TEST_DATA['test_format_render_results_for_graph']['before']
        after = self._TEST_DATA['test_format_render_results_for_graph']['after']
        formatted = server.format_render_results(before)
        formatted_str = json.loads(formatted)
        self.assertEqual(formatted_str, after)
