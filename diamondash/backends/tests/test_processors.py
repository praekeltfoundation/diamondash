from twisted.trial import unittest

from diamondash.backends import processors
from diamondash.backends.processors import (LastDatapointSummarizer,
                                            AggregatingSummarizer)


class SummarizersTestCase(unittest.TestCase):
    def assert_summarizer(self, summarizer, from_time, datapoints, expected):
        self.assertEqual(summarizer(datapoints, from_time), expected)

    def test_time_alignment(self):
        def assert_alignment(bucket_size, t, expected):
            summarizer = processors.Summarizer(bucket_size)
            self.assertEqual(summarizer.align_time(t), expected)

        assert_alignment(5, 2, 0)
        assert_alignment(5, 3, 5)
        assert_alignment(5, 5, 5)
        assert_alignment(5, 6, 5)
        assert_alignment(5, 7, 5)
        assert_alignment(5, 8, 10)
        assert_alignment(5, 9, 10)
        assert_alignment(5, 10, 10)

        assert_alignment(10, 3, 0)
        assert_alignment(10, 5, 10)
        assert_alignment(10, 10, 10)
        assert_alignment(10, 12, 10)
        assert_alignment(10, 13, 10)
        assert_alignment(10, 15, 20)
        assert_alignment(10, 18, 20)

    def test_last_datapoint_summarizer(self):
        self.assert_summarizer(LastDatapointSummarizer(5), 3, [], [])
        self.assert_summarizer(LastDatapointSummarizer(5), 12,
           [{'x': 12, 'y': 3}], [{'x': 10, 'y': 3}])

        self.assert_summarizer(LastDatapointSummarizer(5), 3,
            [
                {'x': 3, 'y': 1},
                {'x': 8, 'y': 2},
                {'x': 11, 'y': 3},
                {'x': 12, 'y': 4},
                {'x': 22, 'y': 6},
                {'x': 28, 'y': 7}
            ],
            [
                {'x': 5, 'y': 1},
                {'x': 10, 'y': 4},
                {'x': 20, 'y': 6},
                {'x': 30, 'y': 7}
            ])

        self.assert_summarizer(LastDatapointSummarizer(5), 8,
            [
                {'x': 8, 'y': 1},
                {'x': 12, 'y': 2},
                {'x': 21, 'y': 3},
                {'x': 22, 'y': 4}
            ],
            [
                {'x': 10, 'y': 2},
                {'x': 20, 'y': 4}
            ])

    def test_aggregating_summarizer(self):
        aggregator = processors.get_aggregator('avg')

        self.assert_summarizer(AggregatingSummarizer(5, aggregator), 3, [], [])
        self.assert_summarizer(AggregatingSummarizer(5, aggregator), 12,
           [{'x': 12, 'y': 3}], [{'x': 10, 'y': 3}])

        self.assert_summarizer(AggregatingSummarizer(5, aggregator), 3,
            [
                {'x': 3, 'y': 1.0},
                {'x': 8, 'y': 2.0},
                {'x': 11, 'y': 3.0},
                {'x': 12, 'y': 4.0},
                {'x': 22, 'y': 6.0},
                {'x': 28, 'y': 7.0}
            ],
            [
                {'x': 5, 'y': 1.0},
                {'x': 10, 'y': 3.0},
                {'x': 20, 'y': 6.0},
                {'x': 30, 'y': 7.0}
            ])

        self.assert_summarizer(AggregatingSummarizer(5, aggregator), 8,
            [
                {'x': 8, 'y': 1.0},
                {'x': 12, 'y': 2.0},
                {'x': 21, 'y': 3.0},
                {'x': 22, 'y': 4.0}
            ],
            [
                {'x': 10, 'y': 1.5},
                {'x': 20, 'y': 3.5}
            ])


class NullFiltersTestCase(unittest.TestCase):
    def assert_null_filter(self, name, datapoints, expected):
        null_filter = processors.get_null_filter(name)
        self.assertEqual(null_filter(datapoints), expected)

    def test_skip_nulls(self):
        self.assert_null_filter('skip',
            [
                {'x': 870, 'y': None},
                {'x': 875, 'y': 0.075312},
                {'x': 885, 'y': 0.033274},
                {'x': 890, 'y': None},
                {'x': 965, 'y': 0.059383},
                {'x': 970, 'y': 0.057101},
                {'x': 975, 'y': 0.056673},
                {'x': 980, 'y': None},
                {'x': 985, 'y': None}
            ],
            [
                {'x': 875, 'y': 0.075312},
                {'x': 885, 'y': 0.033274},
                {'x': 965, 'y': 0.059383},
                {'x': 970, 'y': 0.057101},
                {'x': 975, 'y': 0.056673}
            ])

    def test_zeroize_nulls(self):
        self.assert_null_filter('zeroize',
            [
                {'x': 870, 'y': None},
                {'x': 875, 'y': 0.075312},
                {'x': 885, 'y': 0.033274},
                {'x': 890, 'y': None},
                {'x': 965, 'y': 0.059383},
                {'x': 970, 'y': 0.057101},
                {'x': 975, 'y': 0.056673},
                {'x': 980, 'y': None},
                {'x': 985, 'y': None}
            ],
            [
                {'x': 870, 'y': 0},
                {'x': 875, 'y': 0.075312},
                {'x': 885, 'y': 0.033274},
                {'x': 890, 'y': 0},
                {'x': 965, 'y': 0.059383},
                {'x': 970, 'y': 0.057101},
                {'x': 975, 'y': 0.056673},
                {'x': 980, 'y': 0},
                {'x': 985, 'y': 0}
            ])


class AggregatorsTestCase(unittest.TestCase):
    def assert_aggregator(self, name, values, expected):
        aggregator = processors.get_aggregator(name)
        self.assertEqual(aggregator(values), expected)

    def test_avg(self):
        self.assert_aggregator('avg', [0], 0)
        self.assert_aggregator('avg', [3.0, 2.0, 13.0], 6.0)
        self.assert_aggregator('avg', [7.0, 8.0], 7.5)
        self.assert_aggregator('avg', [2.0, 4.0, 9.0, 8.0], 5.75)
