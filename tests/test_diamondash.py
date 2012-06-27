"""Tests for diamondash's server side"""

from twisted.trial import unittest


class FakeHTTP(Protocol):
    def dataReceived(self, data):
        self.transport.write(self.factory.response_body)
        self.transport.loseConnection()


class MockGraphiteServer(object):
    """
    A 'fake' Graphite server providing metrics from
    pre-collected data in a file
    """

    # TODO implement the test server


class WebServerTester(unittest.TestCase):
    """Tests the diamondash web server functionality"""
    
    #def test_get_data(self):
    #    """Tests whether data is obtained properly"""
        # TODO

    # TODO validate obtained data
