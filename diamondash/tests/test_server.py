"""Tests for diamondash's server side"""

import json
from urllib import urlencode

from pkg_resources import resource_stream
from klein.test_resource import requestMock
from twisted.trial import unittest
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import Protocol, Factory

from diamondash import server
from diamondash.dashboard import Dashboard
from diamondash.server import build_config


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

        if response_data is None:
            response = ['HTTP/1.1 404', '', '']
        else:
            response = ['HTTP/1.1 %s' % (response_data['code'],)]
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


class DiamondashServerTestCase(unittest.TestCase, MockGraphiteServerMixin):

    TEST_DATA = json.load(resource_stream(__name__, 'server_test_data.json'))

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

        test_overrides = {
                'graphite_url': self.graphite_url,
                'render_period': 5
            }

        # initialise the server configuration
        server.config = build_config(test_overrides)

        dashboard_config = {
        'name': 'test-dashboard',
        'widgets': {
                'random-count-sum': {
                    'title': 'a graph',
                    'type': 'graph',
                    'bucket_size': 5,
                    'metrics': {
                        'luke the metric': {
                            'target': 'vumi.random.count.sum'
                         }
                     }
                }
            }
        }
        server.config['dashboards']['test-dashboard'] = Dashboard(dashboard_config)

        input = self.TEST_DATA['test_render_for_graph']['input']
        request = requestMock(input, host=self.graphite_ws.getHost().host,
                              port=self.graphite_ws.getHost().port)
        output = self.TEST_DATA['test_render_for_graph']['output']
        d = server.render(request, 'test-dashboard', 'random-count-sum')
        d.addCallback(self.assert_response, output)
        yield d

    @inlineCallbacks
    def test_render_for_multimetric_graph(self):
        """
        Should build a graphite url from the passed in client
        request, send a request to graphite, apply transformations, 
        and return data useable by the client side
        """
        yield self.start_graphite_ws()

        test_overrides = {
                'graphite_url': self.graphite_url,
                'render_period': 5
            }

        # initialise the server configuration
        server.config = build_config(test_overrides)

        dashboard_config = {
        'name': 'test-dashboard',
        'widgets': {
                'random-count-sum-and-average': {
                    'title': 'a graph',
                    'type': 'graph',
                    'bucket_size': 5,
                    'metrics': {
                        'random-count-sum': {
                            'target': 'vumi.random.count.sum'
                         },
                        'random-timer-average': {
                            'target': 'vumi.random.timer.avg'
                         }
                     }
                }
            }
        }
        server.config['dashboards']['test-dashboard'] = Dashboard(dashboard_config)

        input = self.TEST_DATA['test_render_for_multimetric_graph']['input']
        request = requestMock(input, host=self.graphite_ws.getHost().host,
                              port=self.graphite_ws.getHost().port)
        output = self.TEST_DATA['test_render_for_multimetric_graph']['output']
        d = server.render(request, 'test-dashboard',
                'random-count-sum-and-average')
        d.addCallback(self.assert_response, output)
        yield d

    def test_get_render_result_datapoints(self):
        """
        Should obtain a list of datapoint lists, each list
        corresponding to a metric
        """
        before = self.TEST_DATA['test_get_render_result_datapoints']['before']
        before_str = json.dumps(before)
        result = server.get_render_result_datapoints(before_str)
        after = self.TEST_DATA['test_get_render_result_datapoints']['after']
        self.assertEqual(result, after)

    """
    Url construction tests
    ----------------------
    """

    # TODO url construction tests widget or dashboard not found

    def test_construct_render_url_for_graph(self):
        """
        Should construct render request urls acceptable to graphite
        from a client side graph render request
        """

        test_render_period = 5
        test_graphite_url = 'http://127.0.0.1:8000'
        test_overrides = {
                'graphite_url': test_graphite_url,
                'render_period': test_render_period,
            }

        # initialise the server configuration
        server.config = build_config(test_overrides)

        dashboard_config = {
        'name': 'test-dashboard',
        'widgets': {
                'random-count-sum': {
                    'bucket_size': 4,
                    'title': 'a graph',
                    'type': 'graph',
                    'metrics': {
                        'random count sum': {
                            'target': 'vumi.random.count.sum'
                         }
                     }
                }
            }
        }
        server.config['dashboards']['test-dashboard'] = Dashboard(dashboard_config)

        params = {
            'target': 'summarize(vumi.random.count.sum, "4minutes", "sum")',
            'from': '-%sminutes' % (test_render_period,),
            'format': 'json'
            }
        correct_render_url = "%s/render/?%s" % (test_graphite_url,
                                                urlencode(params))

        constructed_render_url = server.construct_render_url(
            'test-dashboard', 
            'random-count-sum')
        self.assertEqual(constructed_render_url, correct_render_url)

    def test_construct_render_url_for_multimetric_graph(self):
        """
        Should construct render request urls acceptable to graphite
        from a client side graph render request
        """

        test_render_period = 5
        test_graphite_url = 'http://127.0.0.1:8000'
        test_overrides = {
                'graphite_url': test_graphite_url,
                'render_period': test_render_period,
            }

        # initialise the server configuration
        server.config = build_config(test_overrides)

        dashboard_config = {
        'name': 'test-dashboard',
        'widgets': {
                'random-count-sum-and-average': {
                    'bucket_size': 2,
                    'title': 'a graph',
                    'type': 'graph',
                    'metrics': {
                        'random-count-sum': {
                            'target': 'vumi.random.count.sum'
                         },
                        'random-timer-average': {
                            'target': 'vumi.random.timer.avg'
                         }
                     }
                }
            }
        }
        server.config['dashboards']['test-dashboard'] = Dashboard(dashboard_config)

        targets = ['summarize(vumi.random.count.sum, "2minutes", "sum")',
            'summarize(vumi.random.timer.avg, "2minutes", "avg")']

        params = {
            'target': targets,
            'from': '-%sminutes' % (test_render_period,),
            'format': 'json'
            }
        correct_render_url = "%s/render/?%s" % (test_graphite_url,
                                                urlencode(params, True))
        constructed_render_url = server.construct_render_url(
            'test-dashboard', 
            'random-count-sum-and-average')
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
        before = self.TEST_DATA['test_skip_nulls']['before']
        after = self.TEST_DATA['test_skip_nulls']['after']
        purified = server.skip_nulls(before)
        self.assertEqual(purified, after)

    def test_zeroize_nulls(self):
        """
        Should return datapoints without null values by
        skipping coordinates with null x or y values
        """
        before = self.TEST_DATA['test_zeroize_nulls']['before']
        after = self.TEST_DATA['test_zeroize_nulls']['after']
        purified = server.zeroize_nulls(before)
        self.assertEqual(purified, after)

    """
    Formatting tests
    ----------------
    """

    def test_format_render_results_for_graph(self):
        """
        Should format datapoints in graphite's format to 
        datapoints in rickshaw's format
        """

        dashboard_config = {
        'name': 'test-dashboard',
        'widgets': {
                'random-count-sum': {
                    'title': 'a graph',
                    'type': 'graph',
                    'metrics': {
                        'arnold-the-metric': {
                            'target': 'vumi.random.count.sum'
                         }
                     }
                }
            }
        }
        server.config['dashboards']['test-dashboard'] = Dashboard(dashboard_config)

        before = self.TEST_DATA['test_format_render_results_for_graph']['before']
        after = self.TEST_DATA['test_format_render_results_for_graph']['after']
        formatted = server.format_render_results(before, 'test-dashboard', 'random-count-sum')
        formatted_str = json.loads(formatted)
        self.assertEqual(formatted_str, after)

    def test_format_render_results_for_multimetric_graph(self):
        """
        Should format datapoints in graphite's format to 
        datapoints in rickshaw's format
        """
        dashboard_config = {
        'name': 'test-dashboard',
        'widgets': {
                'random-count-sum-and-average': {
                    'title': 'a graph',
                    'type': 'graph',
                    'metrics': {
                        'random-count-sum': {
                            'target': 'vumi.random.count.sum'
                         },
                        'random-timer-average': {
                            'target': 'vumi.random.timer.avg'
                         }
                     }
                }
            }
        }

        server.config['dashboards']['test-dashboard'] = Dashboard(dashboard_config)
        before = self.TEST_DATA['test_format_render_results_for_multimetric_graph']['before']
        after = self.TEST_DATA['test_format_render_results_for_multimetric_graph']['after']
        formatted = server.format_render_results(before, 'test-dashboard',
            'random-count-sum-and-average')
        formatted_str = json.loads(formatted)
        self.assertEqual(formatted_str, after)
