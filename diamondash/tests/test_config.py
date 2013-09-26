import os
import json

from twisted.trial import unittest
from diamondash.config import Config


class ToyConfig(Config):
    KEY = 'toy'
    DEFAULTS = {'foo': 'bar'}

    @classmethod
    def parse(cls, config_dict):
        if 'name' in config_dict:
            config_dict['title'] = config_dict['name'].capitalize()

        return config_dict


class ConfigTestCase(unittest.TestCase):
    def test_registry(self):
        self.assertEqual(Config.REGISTRY['toy'], ToyConfig)

    def test_setting(self):
        config = ToyConfig()
        self.assertTrue('foo' not in config.items)
        config['foo'] = 'bar'
        self.assertEqual(config.items['foo'], 'bar')

    def test_getting(self):
        config = ToyConfig({'foo': 'bar'})
        self.assertEqual(config['foo'], 'bar')

    def test_checking(self):
        config = ToyConfig({'foo': 'bar'})
        self.assertTrue('foo' in config)

    def test_from_args(self):
        config = ToyConfig.from_args(name='thing')
        self.assertEqual(config['foo'], 'bar')
        self.assertEqual(config['name'], 'thing')
        self.assertEqual(config['title'], 'Thing')

    def test_from_dict(self):
        config = ToyConfig.from_dict({'name': 'thing'})
        self.assertEqual(config['foo'], 'bar')
        self.assertEqual(config['name'], 'thing')
        self.assertEqual(config['title'], 'Thing')

    def test_from_file(self):
        config = ToyConfig.from_file(os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'toy_config.yml'))

        self.assertEqual(config['foo'], 'bar')
        self.assertEqual(config['name'], 'luke')
        self.assertEqual(config['title'], 'Luke')

    def test_to_json(self):
        config = ToyConfig({
            'foo': 'bar',
            'baz': 'qux'
        })

        self.assertEqual(config.to_json(), json.dumps({
            'foo': 'bar',
            'baz': 'qux'
        }))
