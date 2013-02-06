class ConfigMixin(object):
    """Mixin which provides a class with configuration infrastructure."""

    __DEFAULTS = {}
    __CONFIG_TAG = 'diamondash.ConfigMixin'

    @classmethod
    def setdefaults(cls, config, defaults):
        """
        Returns a config dict updated with the following dicts:
            - __DEFAULTS: class defaults
            - defaults: configured class defaults (for all classes)
            - config: the original config
        """
        new_config = {}
        new_config.update(cls.__DEFAULTS)
        new_config.update(defaults.get(cls.__CONFIG_TAG, {}))
        new_config.update(config)
        return new_config

    @classmethod
    def from_config(cls, config, defaults={}):
        """
        Parses a config, then returns an instances constructed from the config.
        """
        config = cls.parse_config(config, defaults)
        return cls(**config)

    @classmethod
    def parse_config(cls, config, defaults={}):
        """Parses abackend config, altering it where necessary."""
        return NotImplementedError()


class ConfigError(Exception):
    """Raised when there is an error parsing a configuration"""


class NotImplementedError(Exception):
    """
    Raised when a subclass has not implemented a method of it's abstract
    parent class
    """
