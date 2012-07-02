# -*- coding: utf-8 -*-
"""Tests for diamondash's dashboard"""

import json

from pkg_resources import resource_string, resource_stream, resource_filename
from twisted.trial import unittest

from diamondash import server
from diamondash.dashboard import slugify, Dashboard
from diamondash.exceptions import ConfigError


class DashboardTestCase(unittest.TestCase):

    def test_slugify(self):
        """Should change 'SomethIng_lIke tHis' to 'something-like-this'"""
        self.assertEqual(slugify('SoMeThing_liKe!tHis'), 'something-like-this')

    def test_from_config_file_not_found(self):
        """Should assert an error if the dashboard in the config file has no name"""
        self.assertRaises(ConfigError, Dashboard.from_config_file, 'tests/non_existent_file.yml')

    def test_no_dashboard_name(self):
        """Should assert an error if the dashboard in the config file has no name"""
        self.assertRaises(ConfigError, Dashboard.from_config_file, 'tests/no_dashboard_name.yml')

    def test_widget_title(self):
        """
        Should use the given widget name as the widget title, or set the 
        widget title using a title key if it is explicitly specified, even
        when the two different conventions are mixed in a config file
        """
        config = Dashboard.from_config_file(resource_filename(__name__, 'widget_title.yml')).config
        self.assertEqual(config['widgets']['random-count-sum']['title'], 'random count sum')
        self.assertEqual(config['widgets']['random-timer-average']['title'], 'this is an explicit title')

    def test_no_widget_metrics(self):
        """Should assert an error if a widget in the config file has no name"""
        self.assertRaises(ConfigError, Dashboard.from_config_file, 'tests/no_widget_metrics.yml')
