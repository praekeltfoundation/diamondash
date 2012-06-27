"""Tests for diamondash's server side"""

from twisted.trial import unittest
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import Protocol, Factory
from diamondash import diamondash


class MockGraphiteServerProtocol(Protocol):
    """A protocol for MockGraphiteServerMixin"""

    def dataReceived(self, data):
        response = self.handle_request(data)
        self.transport.write(response)
        self.transport.loseConnection()

    def _parse_request(self, data):
        # TODO
        pass

    def _construct_response(self, response_data):
        # TODO
        pass

    def handle_request(data):
        request_uri, request_body = _parse_request(data)
        response_data = self.factory.response_data.get(request_uri)
        return self._construct_response(response_data)


class MockGraphiteServerMixin(object):
    """
    A mock Graphite server mixin, providing metric data from captured
    Graphite response data
    """

    @inlineCallbacks
    def start_graphite_ws(self, response_data):
        factory = Factory()
        factory.protocol = MockGraphiteServerProtocol
        factory.response_data = response_data
        self.graphite_ws = yield reactor.listenTCP(0, factory)
        address = self.graphite_ws.getHost()
        self.graphite_url = "http://%s:%s/" % (address.host, address.port)

    def stop_graphite_ws(self):
        return self.server.loseConnection()


_GRAPHITE_RESPONSE_DATA = json.load('graphite_response_data.json')
_FORMATTED_DATA = json.load('formatted_data.json')


class DiamondashServerTestCase(unittest.TestCase, MockGraphiteServerMixin):
    """Tests the diamondash web server functionality"""

    def startUp(self):
        self.start_graphite_ws()
        diamondash.graphite_url = self.graphite_url

    def tearDown(self):
        self.stop_graphite_ws()

    def test_invalid_client_request(self):
        """
        Tests whether invalid client requests are
        handled appropriately
        """
        #TODO
        self.assertEqual(1, 0)

    """
    Url construction tests
    ----------------------
    """

    # TODO url construction tests for other widget types

    def test_construct_render_url_for_graph(self):
        """
        Tests whether graphite render request urls are constructed properly
        from client side render requests
        """
        #TODO
        self.assertEqual(1, 0)

    """
    Formatting tests
    ----------------
    """

    # TODO formatting tests for other widget types

    def test_format_render_nulls(self):
        """
        Tests whether null values in graphite render results are
        handled appropriately
        """
        # TODO
        self.assertEqual(1, 0)

    def test_format_render_results_for_graph(self):
        """
        Tests whether graphite render results are formatted
        as expected by the client side for graph widgets
        """
        # TODO
        self.assertEqual(1, 0)
