from twisted.trial import unittest
from diamondash import ConfigMixin


class ConfigMixinTestCase(unittest.TestCase):
    def test_override_class_defaults(self):
        class_defaults = {
            'ClassA': {
                'field1': 21,
                'field2': 23,
            },
            'ClassB': {
                'field1': 'lerp',
            }
        }
        overrides = {
            'ClassA': {
                'field1': 22,
            },
            'ClassB': {
                'field1': 'larp',
            }
        }
        new_class_defaults = ConfigMixin.override_class_defaults(
            class_defaults, overrides)
        self.assertEqual(new_class_defaults, {
            'ClassA': {
                'field1': 22,
                'field2': 23,
            },
            'ClassB': {
                'field1': 'larp',
            }
        })
        self.assertEqual(class_defaults, {
            'ClassA': {
                'field1': 21,
                'field2': 23,
            },
            'ClassB': {
                'field1': 'lerp',
            }
        })
        self.assertEqual(overrides, {
            'ClassA': {
                'field1': 22,
            },
            'ClassB': {
                'field1': 'larp',
            }
        })
