from mock import Mock
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.internet import reactor
from twisted.internet.defer import Deferred, DeferredQueue, inlineCallbacks

from diamondash.backends import Backend


def stub_from_config(cls):
    cls.from_config = Mock(
        side_effect=lambda config, class_defaults: (config, class_defaults))


class ToyBackend(Backend):
    def __init__(self, response_data=[]):
        self.response_data = response_data
        self.get_data_calls = []

    def get_data(self, **params):
        d = Deferred()
        self.get_data_calls.append(params)
        d.addCallback(lambda *a, **kw: self.response_data)
        return d


class MockResource(Resource):
    """Adapted from [vumi](https://github.com/praekelt/vumi)"""

    isLeaf = True

    def __init__(self, handler):
        Resource.__init__(self)
        self.handler = handler

    def render(self, request):
        return self.handler(request)


class MockHttpServer(object):
    """Adapted from [vumi](https://github.com/praekelt/vumi)"""

    def __init__(self, handler=None):
        self.queue = DeferredQueue()
        self._handler = handler or self.handle_request
        self._webserver = None
        self.addr = None
        self.url = None

    def handle_request(self, request):
        self.queue.put(request)

    @inlineCallbacks
    def start(self):
        root = MockResource(self._handler)
        site_factory = Site(root)
        self._webserver = yield reactor.listenTCP(0, site_factory)
        self.addr = self._webserver.getHost()
        self.url = "http://%s:%s/" % (self.addr.host, self.addr.port)

    def stop(self):
        return self._webserver.loseConnection()
