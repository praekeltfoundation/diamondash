import os

from twisted.trial import unittest
from diamondash.config import Config


class ToyConfig(Config):
    KEY = 'toy'
    DEFAULTS = {'eggs': 'ham'}

    @classmethod
    def parse(cls, config_dict):
        if 'name' in config_dict:
            config_dict['title'] = config_dict['name'].capitalize()

        return config_dict


class ToyAConfig(ToyConfig):
    KEY = 'toy_a'
    DEFAULTS = {'pram': 'ram'}


class ToyBConfig(ToyConfig):
    KEY = 'toy_b'
    DEFAULTS = {'eggs': 'spam'}


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

    def test_configs_from_dir(self):
        dirname = os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'toy_configs')

        config_a, config_b = ToyConfig.configs_from_dir(
            dirname,
            foo='bar')

        self.assertEqual(config_a['foo'], 'bar')
        self.assertEqual(config_a['eggs'], 'ham')
        self.assertEqual(config_a['name'], 'luke')
        self.assertEqual(config_a['title'], 'Luke')

        self.assertEqual(config_b['foo'], 'bar')
        self.assertEqual(config_b['eggs'], 'ham')
        self.assertEqual(config_b['name'], 'anakin')
        self.assertEqual(config_b['title'], 'Anakin')
