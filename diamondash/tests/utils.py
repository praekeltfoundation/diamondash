from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.internet import reactor
from twisted.internet.defer import Deferred, DeferredQueue, inlineCallbacks

from diamondash.backends import Backend
from diamondash.widgets.dynamic import DynamicWidgetConfig, DynamicWidget


class ToyBackend(Backend):
    def __init__(self, config):
        super(ToyBackend, self).__init__(config)
        self.response = []
        self.requests = []

    def set_response(self, response):
        self.response = response

    def get_requests(self):
        return self.requests

    def get_data(self, **params):
        d = Deferred()
        self.requests.append(params)
        d.addCallback(lambda *a, **kw: self.response)
        return d


class ToyDynamicWidgetConfig(DynamicWidgetConfig):
    TYPE_NAME = 'dynamic_toy'

    @classmethod
    def parse(cls, config):
        config = super(ToyDynamicWidgetConfig, cls).parse(config)

        config['backend']['metrics'] = config.get('metrics', [])
        backend_config_cls = cls.for_type(config['backend']['type'])
        config['backend'] = backend_config_cls.from_dict(config['backend'])

        return config


class ToyDynamicWidget(DynamicWidget):
    CONFIG_CLS = ToyDynamicWidgetConfig

    def get_snapshot(self):
        return [self.config['name']]


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
