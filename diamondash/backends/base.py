from uuid import uuid4

from diamondash.config import Config, ConfigError


class BackendConfig(Config):
    pass


class Backend(object):
    CONFIG_CLS = BackendConfig

    def __init__(self, config):
        self.config = config


class MetricConfig(Config):
    @classmethod
    def parse(cls, config):
        if 'target' not in config:
            raise ConfigError("All metrics need a target")

        config['id'] = str(uuid4())
        return config


class Metric(object):
    CONFIG_CLS = MetricConfig

    def __init__(self, config):
        self.config = config


class BadBackendResponseError(Exception):
    """
    Should be raised if the backend returns an erroneous response
    """
