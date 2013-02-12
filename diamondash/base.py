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
    def override_class_defaults(cls, class_defaults, overrides={}):
        """
        Takes in `class_defaults` and `overrides` dicts with defaults for
        classes and returns a new dict containing the original defaults for
        each class in `class_defaults` updated with the respective class
        defaults in `overrides`.
        """
        new_class_defaults = {}
        for config_tag, defaults in class_defaults.iteritems():
            new_class_defaults[config_tag] = utils.update_dict(
                overrides.get(config_tag, {}), defaults)

        return new_class_defaults

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
        config = utils.update_dict(config, cls.__DEFAULTS, defaults)
        return config


class ConfigError(Exception):
    """Raised when there is an error parsing a configuration"""
