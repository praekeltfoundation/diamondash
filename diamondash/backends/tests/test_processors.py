from twisted.trial import unittest

from diamondash.backends import processors


class SummarizersTestCase(unittest.TestCase):
    def test_last_datapoint_summarizer_with_round_alignment(self):
        summarizer = processors.summarizers.get('last', 'round', 5)

        self.assertEqual(
            summarizer(3, []),
            [])

        self.assertEqual(
            summarizer(12, [{'x': 12, 'y': 3}]),
            [{'x': 10, 'y': 3}])

        self.assertEqual(
            summarizer(3, [{'x': 12, 'y': 3}]),
            [{'x': 10, 'y': 3}])

        self.assertEqual(
            summarizer(3, [
                {'x': 3, 'y': 1},
                {'x': 8, 'y': 2},
                {'x': 11, 'y': 3},
                {'x': 12, 'y': 4},
                {'x': 22, 'y': 6},
                {'x': 28, 'y': 7}
            ]), [
                {'x': 5, 'y': 1},
                {'x': 10, 'y': 4},
                {'x': 20, 'y': 6},
                {'x': 30, 'y': 7}
            ])

        self.assertEqual(
            summarizer(8, [
                {'x': 8, 'y': 1},
                {'x': 12, 'y': 2},
                {'x': 21, 'y': 3},
                {'x': 22, 'y': 4}
            ]), [
                {'x': 10, 'y': 2},
                {'x': 20, 'y': 4}
            ])

    def test_last_datapoint_summarizer_with_floor_alignment(self):
        summarizer = processors.summarizers.get('last', 'floor', 5)

        self.assertEqual(
            summarizer(12, [{'x': 12, 'y': 3}]),
            [{'x': 10, 'y': 3}])

        self.assertEqual(
            summarizer(3, [
                {'x': 3, 'y': 1},
                {'x': 8, 'y': 2},
                {'x': 11, 'y': 3},
                {'x': 12, 'y': 4},
                {'x': 22, 'y': 6},
                {'x': 28, 'y': 7}
            ]), [
                {'x': 0, 'y': 1},
                {'x': 5, 'y': 2},
                {'x': 10, 'y': 4},
                {'x': 20, 'y': 6},
                {'x': 25, 'y': 7}
            ])

        self.assertEqual(
            summarizer(8, [
                {'x': 8, 'y': 1},
                {'x': 12, 'y': 2},
                {'x': 21, 'y': 3},
                {'x': 22, 'y': 4}
            ]), [
                {'x': 5, 'y': 1},
                {'x': 10, 'y': 2},
                {'x': 20, 'y': 4}
            ])

    def test_aggregating_summarizer_with_round_alignment(self):
        summarizer = processors.summarizers.get('avg', 'round', 5)

        self.assertEqual(
            summarizer(3, []),
            [])

        self.assertEqual(
            summarizer(12, [{'x': 12, 'y': 3}]),
            [{'x': 10, 'y': 3}])

        self.assertEqual(
            summarizer(3, [
                {'x': 3, 'y': 1.0},
                {'x': 8, 'y': 2.0},
                {'x': 11, 'y': 3.0},
                {'x': 12, 'y': 4.0},
                {'x': 22, 'y': 6.0},
                {'x': 28, 'y': 7.0}
            ]), [
                {'x': 5, 'y': 1.0},
                {'x': 10, 'y': 3.0},
                {'x': 20, 'y': 6.0},
                {'x': 30, 'y': 7.0}
            ])

        self.assertEqual(
            summarizer(8, [
                {'x': 8, 'y': 1.0},
                {'x': 12, 'y': 2.0},
                {'x': 21, 'y': 3.0},
                {'x': 22, 'y': 4.0}
            ]), [
                {'x': 10, 'y': 1.5},
                {'x': 20, 'y': 3.5}
            ])

    def test_aggregating_summarizer_with_floor_alignment(self):
        summarizer = processors.summarizers.get('avg', 'floor', 5)

        self.assertEqual(
            summarizer(3, []),
            [])

        self.assertEqual(
            summarizer(12, [{'x': 12, 'y': 3}]),
            [{'x': 10, 'y': 3}])

        self.assertEqual(
            summarizer(3, [
                {'x': 3, 'y': 1.0},
                {'x': 8, 'y': 2.0},
                {'x': 11, 'y': 3.0},
                {'x': 12, 'y': 4.0},
                {'x': 22, 'y': 6.0},
                {'x': 28, 'y': 7.0}
            ]), [
                {'x': 0, 'y': 1.0},
                {'x': 5, 'y': 2.0},
                {'x': 10, 'y': 3.5},
                {'x': 20, 'y': 6.0},
                {'x': 25, 'y': 7.0}
            ])

        self.assertEqual(
            summarizer(8, [
                {'x': 8, 'y': 1.0},
                {'x': 12, 'y': 2.0},
                {'x': 21, 'y': 3.0},
                {'x': 22, 'y': 4.0}
            ]), [
                {'x': 5, 'y': 1.0},
                {'x': 10, 'y': 2.0},
                {'x': 20, 'y': 3.5}
            ])


class NullFiltersTestCase(unittest.TestCase):
    def test_skip_nulls(self):
        filter = processors.null_filters['skip']

        self.assertEqual(
            filter([
                {'x': 870, 'y': None},
                {'x': 875, 'y': 0.075312},
                {'x': 885, 'y': 0.033274},
                {'x': 890, 'y': None},
                {'x': 965, 'y': 0.059383},
                {'x': 970, 'y': 0.057101},
                {'x': 975, 'y': 0.056673},
                {'x': 980, 'y': None},
                {'x': 985, 'y': None}
            ]), [
                {'x': 875, 'y': 0.075312},
                {'x': 885, 'y': 0.033274},
                {'x': 965, 'y': 0.059383},
                {'x': 970, 'y': 0.057101},
                {'x': 975, 'y': 0.056673}
            ])

    def test_zeroize_nulls(self):
        filter = processors.null_filters['zeroize']

        self.assertEqual(
            filter([
                {'x': 870, 'y': None},
                {'x': 875, 'y': 0.075312},
                {'x': 885, 'y': 0.033274},
                {'x': 890, 'y': None},
                {'x': 965, 'y': 0.059383},
                {'x': 970, 'y': 0.057101},
                {'x': 975, 'y': 0.056673},
                {'x': 980, 'y': None},
                {'x': 985, 'y': None}
            ]), [
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
    def test_avg(self):
        aggregator = processors.aggregators['avg']

        self.assertEqual(
            aggregator([0]),
            0)

        self.assertEqual(
            aggregator([3.0, 2.0, 13.0]),
            6.0)

        self.assertEqual(
            aggregator([7.0, 8.0]),
            7.5)

        self.assertEqual(
            aggregator([2.0, 4.0, 9.0, 8.0]),
            5.75)
