from twisted.trial import unittest

from diamondash import utils
from diamondash.widgets.pie import PieWidgetConfig


def mk_config_data(**overrides):
    return utils.add_dicts({
        'name': 'test-chart-widget',
        'graphite_url': 'fake_graphite_url',
        'metrics': [
            {'name': 'random sum', 'target': 'vumi.random.count.sum'},
            {'name': 'random avg', 'target': 'vumi.random.timer.avg'}],
        'time_range': '1d',
        'null_filter': 'zeroize',
        'backend': {'type': 'diamondash.tests.utils.ToyBackend'}
    }, overrides)


class ChartWidgetConfigTestCase(unittest.TestCase):
    def test_parsing(self):
        config = PieWidgetConfig(mk_config_data())
        self.assertEqual(config['bucket_size'], config['time_range'])
