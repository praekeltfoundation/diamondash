from diamondash import ConfigMixin, NotImplementedError
from diamondash import utils


class Backend(ConfigMixin):
    """Abstract backend to provide widgets with data."""

    __DEFAULTS = {}
    __CONFIG_TAG = 'diamondash.backends.Backend'

    @classmethod
    def parse_config(cls, config, class_defaults={}):
        """Parses the backend config, altering it where necessary."""
        defaults = class_defaults.get(cls.__CONFIG_TAG, {})
        config = utils.setdefaults(config, cls.__DEFAULTS, defaults)

        # General backend configuration goes here

        return config

    def get_data(self, **kwargs):
        """
        Returns data from the backend according to the backend's configuration
        and the passed in arguments.
        """
        return NotImplementedError()
