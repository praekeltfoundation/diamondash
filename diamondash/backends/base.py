from diamondash.config import Config


class BackendConfig(Config):
    pass


class Backend(object):
    CONFIG_CLS = BackendConfig

    def __init__(self, config):
        self.config = config


class MetricConfig(Config):
    pass


class Metric(object):
    CONFIG_CLS = MetricConfig

    def __init__(self, config):
        self.config = config


class BadBackendResponseError(Exception):
    """
    Should be raised if the backend returns an erroneous response
    """
