from twisted.trial import unittest

from diamondash import utils
from diamondash.config import ConfigError
from diamondash.backends import MetricConfig


def mk_metric_config_data(**overrides):
    return utils.add_dicts({
        'target': 'a.last',
    }, overrides)


class MetricConfigTestCase(unittest.TestCase):
    def test_parsing_for_no_target(self):
        config = mk_metric_config_data()
        del config['target']
        self.assertRaises(ConfigError, MetricConfig.parse, {})
