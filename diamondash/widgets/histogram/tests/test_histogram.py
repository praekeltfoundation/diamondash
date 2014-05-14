from twisted.trial import unittest

from diamondash import utils
from diamondash.config import ConfigError
from diamondash.widgets.histogram import HistogramWidgetConfig


def mk_config_data(**overrides):
    return utils.add_dicts({
        'name': 'test-histogram',
        'target': 'some.target',
        'time_range': '1d',
        'backend': {'type': 'diamondash.tests.utils.ToyBackend'}
    }, overrides)


class ChartWidgetConfigTestCase(unittest.TestCase):
    def test_parsing(self):
        config = HistogramWidgetConfig(mk_config_data())

        self.assertEqual(config['backend']['bucket_size'], 3600000)
        metric_config, = config['backend']['metrics']
        self.assertEqual(metric_config['target'], 'some.target')
        self.assertEqual(metric_config['name'], 'test-histogram')

    def test_parsing_config_for_no_target(self):
        config = mk_config_data()
        del config['target']

        self.assertRaises(
            ConfigError,
            HistogramWidgetConfig.parse,
            config)
