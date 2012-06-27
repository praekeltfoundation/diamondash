"""Tests for diamondash's server side"""

from twisted.trial import unittest
from twisted.internet.protocol import Protocol

class FakeHTTP(Protocol):
    def dataReceived(self, data):
        self.transport.write(self.factory.response_body)
        self.transport.loseConnection()


class MockGraphiteServer(object):
    """
    #A 'fake' Graphite server providing metrics from
    #pre-collected data in a file
    """

    # TODO implement the test server

class WebServerTester(unittest.TestCase):
    """Tests the diamondash web server functionality"""

    def test_construct_render_url(self):
        """
        Tests whether graphite render request urls are constructed properly
        from client side render requests
        """
        #TODO
        self.assertEqual(1, 0)

    def test_format_render_results(self):
        """
        Tests whether graphite render results are formatted
        as expected by the client side
        """
        # TODO
        self.assertEqual(1, 0)

    def test_format_render_nulls(self):
        """
        Tests whether null values in graphite render results are
        handled appropriately
        """
        # TODO
        self.assertEqual(1, 0)
