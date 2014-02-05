from twisted.python import log

from diamondash import utils
from diamondash.backends import BadBackendResponseError
from diamondash.widgets.widget import Widget, WidgetConfig


class DynamicWidgetConfig(WidgetConfig):
    TYPE_NAME = 'dynamic'
    DEFAULT_BACKEND = 'diamondash.backends.graphite.GraphiteBackend'
    DEFAULT_BACKEND_URL = 'http://127.0.0.1:8080'

    @classmethod
    def parse(cls, config):
        config = super(DynamicWidgetConfig, cls).parse(config)
        config.setdefault('backend', {})
        config['backend'].setdefault('type', cls.DEFAULT_BACKEND)
        config['backend'].setdefault('url', cls.DEFAULT_BACKEND_URL)
        return config


class DynamicWidget(Widget):
    CONFIG_CLS = DynamicWidgetConfig

    def __init__(self, config):
        super(DynamicWidget, self).__init__(config)

        backend_cls = utils.load_class_by_string(config['backend']['type'])
        self.backend = backend_cls(config['backend'])

    def get_snapshot(self):
        """Returns a snapshot of the widget's non-static data."""
        raise NotImplementedError()
