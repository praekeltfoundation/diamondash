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
            utils.update_dict(defaults, original), {'a': 1, 'b': 2})
        self.assertEqual(original, {'a': 1})
        self.assertEqual(defaults, {'a': 0, 'b': 2})

        original = {'a': 1}
        defaults1 = {'a': 0, 'b': 2}
        defaults2 = {'b': 3, 'c': 4}
        self.assertEqual(
            utils.update_dict(defaults1, defaults2, original),
            {'a': 1, 'b': 3, 'c': 4})
        self.assertEqual(original, {'a': 1})
        self.assertEqual(defaults1, {'a': 0, 'b': 2})
        self.assertEqual(defaults2, {'b': 3, 'c': 4})

    def test_round_time(self):
        self.assertEqual(utils.round_time(2, 5), 0)
        self.assertEqual(utils.round_time(3, 5), 5)
        self.assertEqual(utils.round_time(5, 5), 5)
        self.assertEqual(utils.round_time(6, 5), 5)
        self.assertEqual(utils.round_time(7, 5), 5)
        self.assertEqual(utils.round_time(8, 5), 10)
        self.assertEqual(utils.round_time(9, 5), 10)
        self.assertEqual(utils.round_time(10, 5), 10)

        self.assertEqual(utils.round_time(3, 10), 0)
        self.assertEqual(utils.round_time(5, 10), 10)
        self.assertEqual(utils.round_time(10, 10), 10)
        self.assertEqual(utils.round_time(12, 10), 10)
        self.assertEqual(utils.round_time(13, 10), 10)
        self.assertEqual(utils.round_time(15, 10), 20)
        self.assertEqual(utils.round_time(18, 10), 20)

    def test_floor_time(self):
        self.assertEqual(utils.floor_time(2, 5), 0)
        self.assertEqual(utils.floor_time(3, 5), 0)
        self.assertEqual(utils.floor_time(5, 5), 5)
        self.assertEqual(utils.floor_time(6, 5), 5)
        self.assertEqual(utils.floor_time(7, 5), 5)
        self.assertEqual(utils.floor_time(8, 5), 5)
        self.assertEqual(utils.floor_time(9, 5), 5)
        self.assertEqual(utils.floor_time(10, 5), 10)

        self.assertEqual(utils.floor_time(3, 10), 0)
        self.assertEqual(utils.floor_time(5, 10), 0)
        self.assertEqual(utils.floor_time(10, 10), 10)
        self.assertEqual(utils.floor_time(12, 10), 10)
        self.assertEqual(utils.floor_time(13, 10), 10)
        self.assertEqual(utils.floor_time(15, 10), 10)
        self.assertEqual(utils.floor_time(18, 10), 10)
        self.assertEqual(utils.floor_time(22, 10), 20)
