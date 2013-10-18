import json
from urllib import urlencode

from twisted.web import http
from twisted.trial import unittest
from twisted.internet.defer import inlineCallbacks

from diamondash import utils
from diamondash.tests.utils import MockHttpServer


class UtilsTestCase(unittest.TestCase):
    def test_isint(self):
        """
        Should check if a number is equivalent to an integer
        """
        self.assertTrue(utils.isint(1))
        self.assertTrue(utils.isint(2.000))
        self.assertTrue(utils.isint(82734.0000000))
        self.assertTrue(utils.isint(-213.0))
        self.assertFalse(utils.isint(23123.123123))

    def test_slugify(self):
        """Should change 'SomethIng_lIke tHis' to 'something-like-this'"""
        self.assertEqual(utils.slugify(u'SoMeThing_liKe!tHis'),
                         'something-like-this')
        self.assertEqual(utils.slugify(u'Godspeed You! Black Emperor'),
                         'godspeed-you-black-emperor')

    def test_parse_interval(self):
        """
        Multiplier-suffixed intervals should be turned into integers correctly.
        """
        self.assertEqual(2, utils.parse_interval(2))
        self.assertEqual(2, utils.parse_interval("2"))
        self.assertEqual(2 * 1000, utils.parse_interval("2s"))
        self.assertEqual(120 * 1000, utils.parse_interval("2m"))
        self.assertEqual(7200 * 1000, utils.parse_interval("2h"))
        self.assertEqual(86400 * 1000 * 2, utils.parse_interval("2d"))

    def test_add_dicts(self):
        original = {'a': 1}
        defaults = {'a': 0, 'b': 2}
        self.assertEqual(
            utils.add_dicts(defaults, original), {'a': 1, 'b': 2})
        self.assertEqual(original, {'a': 1})
        self.assertEqual(defaults, {'a': 0, 'b': 2})

        original = {'a': 1}
        defaults1 = {'a': 0, 'b': 2}
        defaults2 = {'b': 3, 'c': 4}
        self.assertEqual(
            utils.add_dicts(defaults1, defaults2, original),
            {'a': 1, 'b': 3, 'c': 4})
        self.assertEqual(original, {'a': 1})
        self.assertEqual(defaults1, {'a': 0, 'b': 2})
        self.assertEqual(defaults2, {'b': 3, 'c': 4})

    def test_round_time(self):
        self.assertEqual(utils.round_time(2, 5), 0)
        self.assertEqual(utils.round_time(3, 5), 5)
        self.assertEqual(utils.round_time(5, 5), 5)
        self.assertEqual(utils.round_time(6, 5), 5)
        self.assertEqual(utils.round_time(7, 5), 5)
        self.assertEqual(utils.round_time(8, 5), 10)
        self.assertEqual(utils.round_time(9, 5), 10)
        self.assertEqual(utils.round_time(10, 5), 10)

        self.assertEqual(utils.round_time(3, 10), 0)
        self.assertEqual(utils.round_time(5, 10), 10)
        self.assertEqual(utils.round_time(10, 10), 10)
        self.assertEqual(utils.round_time(12, 10), 10)
        self.assertEqual(utils.round_time(13, 10), 10)
        self.assertEqual(utils.round_time(15, 10), 20)
        self.assertEqual(utils.round_time(18, 10), 20)

    def test_floor_time(self):
        self.assertEqual(utils.floor_time(2, 5), 0)
        self.assertEqual(utils.floor_time(3, 5), 0)
        self.assertEqual(utils.floor_time(5, 5), 5)
        self.assertEqual(utils.floor_time(6, 5), 5)
        self.assertEqual(utils.floor_time(7, 5), 5)
        self.assertEqual(utils.floor_time(8, 5), 5)
        self.assertEqual(utils.floor_time(9, 5), 5)
        self.assertEqual(utils.floor_time(10, 5), 10)

        self.assertEqual(utils.floor_time(3, 10), 0)
        self.assertEqual(utils.floor_time(5, 10), 0)
        self.assertEqual(utils.floor_time(10, 10), 10)
        self.assertEqual(utils.floor_time(12, 10), 10)
        self.assertEqual(utils.floor_time(13, 10), 10)
        self.assertEqual(utils.floor_time(15, 10), 10)
        self.assertEqual(utils.floor_time(18, 10), 10)
        self.assertEqual(utils.floor_time(22, 10), 20)


class HttpUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.set_response_data("", http.OK, {})
        self.server = MockHttpServer(handler=self.handle_request)
        return self.server.start()

    def tearDown(self):
        return self.server.stop()

    def set_response_data(self, body, code, headers):
        self.response_body = body
        self.response_code = code
        self.response_headers = headers

    @inlineCallbacks
    def assert_last_request(self, args, data="", headers={}, method='GET'):
        request = yield self.server.queue.get()
        self.assertEqual(request.content.read(), data)
        self.assertEqual(request.method, method)
        self.assertEqual(request.args, args)

        for k, v in headers.iteritems():
            self.assertEqual(request.requestHeaders.getRawHeaders(k), v)

    def handle_request(self, request):
        request.setResponseCode(self.response_code)
        for h_name, h_values in self.response_headers.iteritems():
            request.responseHeaders.setRawHeaders(h_name, h_values)
        self.server.queue.put(request)
        return self.response_body

    def assert_happy_response(self, body, code=http.OK, headers={}):
        self.set_response_data(body, code, headers)
        d = utils.http_request(self.server.url)

        def assert_response(response):
            self.assertEqual(response['body'], body)
            self.assertEqual(response['status'], str(code))
            for k, v in headers.iteritems():
                self.assertEqual(response['headers'][k], v)
        d.addCallback(assert_response)
        return d

    def assert_response(self, body, code=http.OK, headers={}):
        self.set_response_data(body, code, headers)
        d = utils.http_request(self.server.url)

        def got_response(response):
            self.assertEqual(response['body'], body)
            self.assertEqual(response['status'], str(code))
            for k, v in headers.iteritems():
                self.assertEqual(response['headers'][k], v)
        d.addCallback(got_response)
        return d

    @inlineCallbacks
    def test_http_request_response_handling(self):
        yield self.assert_response("")
        yield self.assert_response(
            json.dumps({'a': [1, 2]}),
            code=http.CREATED,
            headers={'luke': ['Skywalker']})

    def test_http_request_for_GET(self):
        utils.http_request(
            "%s?%s" % (self.server.url, urlencode({'a': 'lerp', 'b': 'larp'})),
            headers={'Han': 'Solo', 'Mon': 'Mothma'},
            method='GET')
        return self.assert_last_request(
            args={'a': ['lerp'], 'b': ['larp']},
            headers={'Han': ['Solo'], 'Mon': ['Mothma']},
            method='GET')

    def test_http_request_for_POST(self):
        data = json.dumps({'a': 'lerp', 'b': 'larp'})
        utils.http_request(self.server.url, data=data, method='POST')
        return self.assert_last_request(args={}, data=data, method='POST')

    def test_http_request_for_DELETE(self):
        data = json.dumps({'a': 'lerp', 'b': 'larp'})
        utils.http_request(self.server.url, data=data, method='DELETE')
        return self.assert_last_request(args={}, data=data, method='DELETE')
