import yaml
import json

from diamondash import utils


class ConfigRegistry(object):
    def __init__(self):
        self.configs = {}

    def register(self, config_type):
        self.configs[config_type.KEY] = config_type

    def unregister(self, config_type):
        del self.configs[config_type.KEY]

    def __getitem__(self, key):
        return self.configs[key]


class ConfigMetaClass(type):
    def __new__(mcs, name, bases, dict):
        cls = type.__new__(mcs, name, bases, dict)
        cls.REGISTRY.register(cls)
        return cls


class Config(object):
    __metaclass__ = ConfigMetaClass

    # Override with a string representing the key used to lookup configuration
    # and defaults relevant for the config type
    KEY = 'base'

    DEFAULTS = {}

    REGISTRY = ConfigRegistry()

    def __init__(self, items=None):
        self.items = items or {}

    def __contains__(self, key):
        return key in self.items

    def __getitem__(self, key):
        return self.items[key]

    def __setitem__(self, key, value):
        self.items[key] = value

    @classmethod
    def from_args(cls, **kwargs):
        return cls.from_dict(kwargs)

    @classmethod
    def from_dict(cls, config_dict):
        config_dict = utils.update_dict(cls.DEFAULTS, config_dict)
        return cls(cls.parse(config_dict))

    @classmethod
    def from_file(cls, filename):
        config_dict = yaml.safe_load(open(filename))
        return cls.from_dict(config_dict)

    @classmethod
    def parse(cls, config_dict):
        return config_dict

    def to_json(self):
        return json.dumps(self.items)
