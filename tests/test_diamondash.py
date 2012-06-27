"""Tests for diamondash's server side"""

from twisted.trial import unittest
from twisted.internet.protocol import Protocol


class MockGraphiteServerProtocol(Protocol):
    """A protocol for MockGraphiteServerMixin"""


class MockGraphiteServerMixin(object):
    """
    A mock Graphite server mixin, providing metric data from
    pre-collected data in a file
    """


class WebServerTester(unittest.TestCase, MockGraphiteServerMixin):
    """Tests the diamondash web server functionality"""

    def startUp(self):
        pass

    def tearDown(self):
        pass

    def test_invalid_client_request(self):
        """
        Tests whether invalid client requests are
        handled appropriately
        """
        #TODO
        self.assertEqual(1, 0)

    def test_format_render_nulls(self):
        """
        Tests whether null values in graphite render results are
        handled appropriately
        """
        # TODO
        self.assertEqual(1, 0)

    """ 
    Url tests for each widget type 
    ------------------------------
    """

    def test_construct_render_url_graph(self):
        """
        Tests whether graphite render request urls are constructed properly
        from client side render requests
        """
        #TODO
        self.assertEqual(1, 0)

    """ 
    Format tests for each widget type 
    ---------------------------------
    """

    def test_format_render_results_graph(self):
        """
        Tests whether graphite render results are formatted
        as expected by the client side
        """
        # TODO
        self.assertEqual(1, 0)
