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

    @classmethod
    def parse(cls, items):
        return items

    @classmethod
    def _parse(cls, items):
        items = utils.add_dicts(cls.DEFAULTS, items)
        return cls.parse(items)

    @classmethod
    def from_dict(cls, items):
        return cls(cls._parse(items or {}))

    @classmethod
    def from_file(cls, filename, **defaults):
        items = utils.add_dicts(defaults, yaml.safe_load(open(filename)))
        return cls.from_dict(items)

    @classmethod
    def for_type(cls, type_name):
        type_cls = utils.load_class_by_string(type_name)
        return type_cls.CONFIG_CLS
