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
        }

        # initialise the server configuration
        server.config = build_config(test_overrides)

        test_render_period = 3600
        dashboard_config = {
            'name': 'test-dashboard',
            'render_period': test_render_period,
            'widgets': {
                'random-count-sum': {
                    'title': 'a graph',
                    'type': 'graph',
                    'bucket_size': 300,
                    'metrics': {
                        'luke the metric': {
                            'target': 'vumi.random.count.sum'
                        }
                    }
                }
            }
        }

        dashboard_configs = server.config['dashboards']
        dashboard_configs['test-dashboard'] = Dashboard(dashboard_config)

        test_data_key = 'test_render_for_graph'
        input = self.TEST_DATA[test_data_key]['input']
        request = requestMock(input, host=self.graphite_ws.getHost().host,
                              port=self.graphite_ws.getHost().port)
        output = self.TEST_DATA[test_data_key]['output']
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
        }

        # initialise the server configuration
        server.config = build_config(test_overrides)

        test_render_period = 3600
        dashboard_config = {
            'name': 'test-dashboard',
            'render_period': test_render_period,
            'widgets': {
                'random-count-sum-and-average': {
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
                    }
                }
            }
        }
        dashboard_configs = server.config['dashboards']
        dashboard_configs['test-dashboard'] = Dashboard(dashboard_config)

        test_data_key = 'test_render_for_multimetric_graph'
        input = self.TEST_DATA[test_data_key]['input']
        request = requestMock(input, host=self.graphite_ws.getHost().host,
                              port=self.graphite_ws.getHost().port)
        output = self.TEST_DATA[test_data_key]['output']
        d = server.render(request, 'test-dashboard',
                          'random-count-sum-and-average')
        d.addCallback(self.assert_response, output)
        yield d

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

        test_graphite_url = 'http://127.0.0.1:8000'
        test_overrides = {
            'graphite_url': test_graphite_url,
        }

        # initialise the server configuration
        server.config = build_config(test_overrides)

        target = 'summarize(vumi.random.count.sum, "240s", "sum")'
        test_render_period = 3600
        widget_config = {
            'title': 'a graph',
            'type': 'graph',
            'bucket_size': 240,
            'render_period': test_render_period,
            'metrics': {
                'random-count-sum': {
                    'target': target
                }
            }
        }

        params = {
            'target': target,
            'from': '-%ss' % (test_render_period,),
            'format': 'json'
        }
        correct_render_url = "%s/render/?%s" % (test_graphite_url,
                                                urlencode(params))

        constructed_render_url = server.construct_render_url(widget_config)
        self.assertEqual(constructed_render_url, correct_render_url)

    def test_construct_render_url_for_multimetric_graph(self):
        """
        Should construct render request urls acceptable to graphite
        from a client side graph render request
        """

        test_graphite_url = 'http://127.0.0.1:8000'
        test_overrides = {
            'graphite_url': test_graphite_url,
        }

        # initialise the server configuration
        server.config = build_config(test_overrides)

        test_render_period = 3600
        targets = ['summarize(vumi.random.count.sum, "120s", "sum")',
                   'summarize(vumi.random.timer.avg, "120s", "avg")']
        widget_config = {
            'title': 'a graph',
            'type': 'graph',
            'render_period': test_render_period,
            'bucket_size': 120,
            'metrics': {
                'random-count-sum': {
                    'target': targets[0]
                },
                'random-timer-average': {
                    'target': targets[1]
                }
            }
        }

        params = {
            'target': targets,
            'from': '-%ss' % (test_render_period,),
            'format': 'json'
        }
        correct_render_url = "%s/render/?%s" % (test_graphite_url,
                                                urlencode(params, True))
        constructed_render_url = server.construct_render_url(widget_config)
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
            }
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
            }
        }

        test_data_key = 'test_format_results_for_multimetric_graph'
        before = self.TEST_DATA[test_data_key]['before']
        after = self.TEST_DATA[test_data_key]['after']
        formatted = server.format_results_for_graph(before, widget_config)
        formatted_str = json.loads(formatted)
        self.assertEqual(formatted_str, after)
