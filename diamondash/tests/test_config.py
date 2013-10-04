import os

from twisted.trial import unittest
from diamondash.config import Config, Configurable


class ToyConfig(Config):
    DEFAULTS = {'eggs': 'ham'}

    @classmethod
    def parse(cls, config_dict):
        if 'name' in config_dict:
            config_dict['title'] = config_dict['name'].capitalize()

        return config_dict


class ToyAConfig(ToyConfig):
    DEFAULTS = {'pram': 'ram'}


class ToyBConfig(ToyConfig):
    DEFAULTS = {'eggs': 'spam'}


class ToyConfigurable(Configurable):
    CONFIG_CLS = ToyConfig


class ConfigTestCase(unittest.TestCase):
    def test_config_type_defaults_inheritance(self):
        self.assertEqual(ToyAConfig.DEFAULTS, {
            'pram': 'ram',
            'eggs': 'ham',
        })

        self.assertEqual(ToyBConfig.DEFAULTS, {
            'eggs': 'spam',
        })

    def test_from_file(self):
        filename = os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'toy_configs',
            'toy_config.yml')

        config = ToyConfig.from_file(
            filename,
            foo='bar',
            eggs='spam')

        self.assertEqual(config['foo'], 'bar')
        self.assertEqual(config['eggs'], 'spam')
        self.assertEqual(config['name'], 'luke')
        self.assertEqual(config['title'], 'Luke')

    def test_from_type(self):
        config = Config.from_type({
            'type': 'diamondash.tests.test_config.ToyConfigurable'
        })
        self.assertTrue(isinstance(config, ToyConfig))

    def test_from_type_for_no_type(self):
        self.assertRaises(KeyError, ToyConfig.from_type, {})

    def test_to_type(self):
        config = ToyConfig({
            'type': 'diamondash.tests.test_config.ToyConfigurable'
        })
        self.assertTrue(isinstance(config.to_type(), ToyConfigurable))

    def test_to_type_for_no_type(self):
        config = ToyConfig()
        self.assertRaises(KeyError, config.to_type)
