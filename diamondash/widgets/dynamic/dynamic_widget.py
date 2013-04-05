from twisted.python import log

from diamondash.widgets.widget import Widget
from diamondash.backends import BadBackendResponseError


class DynamicWidget(Widget):
    __DEFAULTS = {}
    __CONFIG_TAG = 'diamondash.widgets.dynamic.DynamicWidget'

    def __init__(self, backend, time_range, **kwargs):
        super(DynamicWidget, self).__init__(**kwargs)
        self.backend = backend
        self.time_range = time_range

    def handle_bad_backend_response(self, failure):
        failure.trap(BadBackendResponseError)
        log.msg(failure)
        return "{}"
