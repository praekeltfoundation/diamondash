import yaml

from diamondash import utils


class ConfigError(Exception):
    """Raised when there is an error parsing a configuration"""


class ConfigMetaClass(type):
    def __new__(mcs, name, bases, dict):
        cls = type.__new__(mcs, name, bases, dict)

        defaults = {}
        for base in bases:
            if hasattr(base, 'DEFAULTS'):
                defaults.update(base.DEFAULTS)

        defaults.update(cls.DEFAULTS)
        cls.DEFAULTS = defaults

        return cls


class Config(dict):
    __metaclass__ = ConfigMetaClass
    DEFAULTS = {}

    def __init__(self, items=None):
        super(Config, self).__init__(self._parse(items or {}))

    @classmethod
    def _parse(cls, items):
        items = utils.add_dicts(cls.DEFAULTS, items)
        return cls.parse(items)

    @classmethod
    def parse(cls, items):
        return items

    @classmethod
    def from_file(cls, filename, **defaults):
        items = utils.add_dicts(defaults, yaml.safe_load(open(filename)))
        return cls(items)

    @classmethod
    def from_type(cls, config):
        if 'type' not in config:
            raise KeyError(
                "Config needs a dict to contain a 'type' key in order to be "
                "constructed from a type")

        type_cls = utils.load_class_by_string(config['type'])
        return type_cls.CONFIG_CLS(config)

    def to_type(self, *args, **kwargs):
        if 'type' not in self:
            raise KeyError(
                "Config instance needs a 'type' key in order to "
                "construct a type")

        type_cls = utils.load_class_by_string(self['type'])
        return type_cls(config=self, *args, **kwargs)


class Configurable(object):
    CONFIG_CLS = Config

    def __init__(self, config):
        self.config = config
