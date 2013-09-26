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

    def test_merge_defaults(self):
        old = {'toy': {'foo': 'bar'}}
        new = {'toy': {'baz': 'qux'}}

        self.assertEqual(
            ToyConfig.merge_defaults(old, new),
            {'toy': {'foo': 'bar', 'baz': 'qux'}})

        self.assertEqual(old, {'toy': {'foo': 'bar'}})
        self.assertEqual(new, {'toy': {'baz': 'qux'}})

    def test_from_dict_defaults(self):
        config = ToyConfig.from_dict({
            'defaults': {
                'toy': {'name': 'thing'}
            }
        })

        self.assertEqual(config['name'], 'thing')
        self.assertEqual(config['title'], 'Thing')

    def test_from_file(self):
        filename = os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'toy_configs',
            'toy_config.yml')

        config = ToyConfig.from_file(
            filename,
            defaults={'toy': {'baz': 'qux'}})

        self.assertEqual(config['foo'], 'bar')
        self.assertEqual(config['baz'], 'qux')
        self.assertEqual(config['lerp'], 'larp')

        self.assertEqual(config['name'], 'luke')
        self.assertEqual(config['title'], 'Luke')

    def test_configs_from_dir(self):
        dirname = os.path.join(
            os.path.dirname(__file__),
            'fixtures',
            'toy_configs')

        config_a, config_b = ToyConfig.configs_from_dir(
            dirname,
            defaults={'toy': {'baz': 'qux'}})

        self.assertEqual(config_a['foo'], 'bar')
        self.assertEqual(config_a['baz'], 'qux')
        self.assertEqual(config_a['lerp'], 'larp')
        self.assertEqual(config_a['name'], 'luke')
        self.assertEqual(config_a['title'], 'Luke')

        self.assertEqual(config_b['foo'], 'bar')
        self.assertEqual(config_b['baz'], 'qux')
        self.assertEqual(config_b['name'], 'anakin')
        self.assertEqual(config_b['title'], 'Anakin')

    def test_to_json(self):
        config = ToyConfig({
            'foo': 'bar',
            'baz': 'qux'
        })

        self.assertEqual(config.to_json(), json.dumps({
            'foo': 'bar',
            'baz': 'qux'
        }))
