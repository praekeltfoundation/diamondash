from mock import Mock
from twisted.internet.defer import Deferred

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
