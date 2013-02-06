from diamondash import utils


class ConfigMixin(object):
    """Mixin which provides a class with configuration infrastructure."""

    # The class variables are made 'private' to not be overriden by subclasses,
    # allowing all classes to have their own set of defaults and their own
    # config tag.
    __DEFAULTS = {}

    # The key used to get defaults for a particular class from the
    # `class_defaults` dict passed to `from_config()` and `parse_config()`
    __CONFIG_TAG = 'diamondash.ConfigMixin'

    @classmethod
    def from_config(cls, config, class_defaults={}):
        """
        Parses a config, then returns an instances constructed from the config.
        """
        config = cls.parse_config(config, class_defaults)
        return cls(**config)

    @classmethod
    def parse_config(cls, config, class_defaults={}):
        """Parses a config, altering it where necessary."""
        defaults = class_defaults.get(cls.__CONFIG_TAG, {})
        config = utils.setdefaults(config, cls.__DEFAULTS, defaults)
        return config


class ConfigError(Exception):
    """Raised when there is an error parsing a configuration"""


class NotImplementedError(Exception):
    """
    Raised when a subclass has not implemented a method of it's abstract
    parent class
    """
