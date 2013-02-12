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
        self.assertEqual(utils.slugify(u'SoMeThing_liKe!tHis'),
                         'something-like-this')
        self.assertEqual(utils.slugify(u'Godspeed You! Black Emperor'),
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

    def test_update_dict(self):
        original = {'a': 1}
        defaults = {'a': 0, 'b': 2}
        self.assertEqual(
            utils.update_dict(original, defaults), {'a': 1, 'b': 2})
        self.assertEqual(original, {'a': 1})
        self.assertEqual(defaults, {'a': 0, 'b': 2})

        original = {'a': 1}
        defaults1 = {'a': 0, 'b': 2}
        defaults2 = {'b': 3, 'c': 4}
        self.assertEqual(
            utils.update_dict(original, defaults1, defaults2),
            {'a': 1, 'b': 3, 'c': 4})
        self.assertEqual(original, {'a': 1})
        self.assertEqual(defaults1, {'a': 0, 'b': 2})
        self.assertEqual(defaults2, {'b': 3, 'c': 4})
