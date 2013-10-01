import yaml
import json
from os import path
from glob import glob

from diamondash import utils


class ConfigError(Exception):
    """Raised when there is an error parsing a configuration"""


class ConfigMetaClass(type):
    def __new__(mcs, name, bases, dict):
        cls = type.__new__(mcs, name, bases, dict)

        defaults = {}
        for base in bases:
            if base is not object:
                defaults.update(base.DEFAULTS)

        defaults.update(cls.DEFAULTS)
        cls.DEFAULTS = defaults

        return cls


class Config(object):
    __metaclass__ = ConfigMetaClass

    DEFAULTS = {}

    def __init__(self, items=None):
        self._items = self._parse(items or {})

    def __contains__(self, key):
        return key in self._items

    def __getitem__(self, key):
        return self._items[key]

    def __setitem__(self, key, value):
        self._items[key] = value

    @classmethod
    def _parse(cls, items):
        items = utils.update_dict(cls.DEFAULTS, items)
        return cls.parse(items)

    @classmethod
    def parse(cls, items):
        return items

    @classmethod
    def from_file(cls, filename):
        return cls(yaml.safe_load(open(filename)))

    @classmethod
    def configs_from_dir(cls, dirname):
        return [
            cls.from_file(filepath)
            for filepath in glob(path.join(dirname, "*.yml"))]

    @classmethod
    def from_type(cls, type_str, config=None):
        type_cls = utils.load_class_by_string(type_str)
        return type_cls.CONFIG_CLS(config)

    def to_type(self, **kwargs):
        if 'type' not in self:
            raise KeyError(
                "Config instance needs a 'type' key in order to "
                "construct a type")

        type_cls = utils.load_class_by_string(self['type'])
        return type_cls(config=self, **kwargs)

    def to_dict(self):
        data = {}

        for key, value in self._items.items():
            if isinstance(value, Config):
                data[key] = value.to_dict()
            else:
                data[key] = value

        return data

    def to_json(self):
        return json.dumps(self.to_dict())


class Configurable(object):
    CONFIG_TYPE = Config

    def __init__(self, config):
        self.config = config

    @classmethod
    def from_dict(cls, config_dict):
        return cls(cls.CONFIG_TYPE(config_dict))
