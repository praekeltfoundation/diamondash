from twisted.trial import unittest

from diamondash import utils


class UtilsTestCase(unittest.TestCase):
    def test_isint(self):
        """
        Should check if a number is equivalent to an integer
        """
        self.assertTrue(utils.isint(1))
        self.assertTrue(utils.isint(2.000))
        self.assertTrue(utils.isint(82734.0000000))
        self.assertTrue(utils.isint(-213.0))
        self.assertFalse(utils.isint(23123.123123))

    def test_slugify(self):
        """Should change 'SomethIng_lIke tHis' to 'something-like-this'"""
        self.assertEqual(utils.slugify('SoMeThing_liKe!tHis'),
                         'something-like-this')
        self.assertEqual(utils.slugify('Godspeed You! Black Emperor'),
                         'godspeed-you-black-emperor')

    def test_parse_interval(self):
        """
        Multiplier-suffixed intervals should be turned into integers correctly.
        """
        self.assertEqual(2, utils.parse_interval(2))
        self.assertEqual(2, utils.parse_interval("2"))
        self.assertEqual(2, utils.parse_interval("2s"))
        self.assertEqual(120, utils.parse_interval("2m"))
        self.assertEqual(7200, utils.parse_interval("2h"))
        self.assertEqual(86400 * 2, utils.parse_interval("2d"))

    def test_set_key_defaults(self):
        """
        Should return a dict with the appropriate key's defaults, overidden
        with the original dict.
        """
        config = {'some_config_option': 23}
        defaults = {
            'a': {
                'some_config_option': 42,
                'some_other_config_option': 182,
            },
            'b': {
                'some_config_option': 22,
                'another_config_option': 21,
            },
        }

        new_config = utils.set_key_defaults('a', config, defaults)

        self.assertEqual(new_config, {
            'some_config_option': 23,
            'some_other_config_option': 182,
        })

        self.assertEqual(config, {'some_config_option': 23})

        self.assertEqual(defaults, {
            'a': {
                'some_config_option': 42,
                'some_other_config_option': 182,
            },
            'b': {
                'some_config_option': 22,
                'another_config_option': 21,
            },
        })

    def test_setdefaults(self):
        original = {'a': 1}
        defaults = {'a': 0, 'b': 2}
        self.assertEqual(
            utils.setdefaults(original, defaults), {'a': 1, 'b': 2})
        self.assertEqual(original, {'a': 1})
        self.assertEqual(defaults, {'a': 0, 'b': 2})

    def test_find_dict_by_item(self):
        def assert_dict(dict_list, key, value, expected_dict):
            self.assertEqual(utils.find_dict_by_item(dict_list, key, value),
                             expected_dict)

        assert_dict(
            [{'a': 1, 'b': 2, 'c': 3},
             {'a': 2, 'b': 4, 'c': 6},
             {'a': 3, 'b': 6, 'c': 9}],
            'b', 4,
             {'a': 2, 'b': 4, 'c': 6})

        assert_dict(
            [{'a': 1, 'b': 2, 'c': 3},
             {'a': 2, 'b': 4, 'c': 6},
             {'a': 3, 'b': 6, 'c': 9}],
            'b', 8,
            None)
