# -*- coding: utf-8 -*-
"""Tests for diamondash's dashboard"""

import json
from diamondash import server
from diamondash.dashboard import slugify, Dashboard
from diamondash.exceptions import ConfigError
from twisted.trial import unittest


class DashboardTestCase(unittest.TestCase):

    def test_slugify(self):
        """Should change 'SomethIng_lIke tHis' to 'something-like-this'"""
        self.assertEqual(slugify('SoMeThing_liKe!tHis'), 'something-like-this')

    def test_from_config_file_not_found(self):
        """Should assert an error if the dashboard in the config file has no name"""
        self.assertRaises(ConfigError, Dashboard.from_config_file, 
                          'tests/non_existent_file.yml')
    def test_no_dashboard_name(self):
        """Should assert an error if the dashboard in the config file has no name"""
        self.assertRaises(ConfigError, Dashboard.from_config_file, 
                          'tests/no_dashboard_name.yml')

    def test_no_widget_name(self):
        """Should assert an error if a widget in the config file has no name"""
        self.assertRaises(ConfigError, Dashboard.from_config_file, 
                          'tests/no_widget_name.yml')

    def test_no_widget_title(self):
        """Should assert an error if a widget in the config file has no name"""
        self.assertRaises(ConfigError, Dashboard.from_config_file, 
                          'tests/no_widget_title.yml')

    def test_no_widget_metric(self):
        """Should assert an error if a widget in the config file has no name"""
        self.assertRaises(ConfigError, Dashboard.from_config_file, 
                          'tests/no_widget_metric.yml')
