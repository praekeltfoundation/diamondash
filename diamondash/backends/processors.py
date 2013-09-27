from diamondash import utils


def skip_nulls(datapoints):
    return [
        d for d in datapoints
        if d['y'] is not None and d['x'] is not None]


def zeroize_nulls(datapoints):
    return [
        d if d['y'] is not None else {'x': d['x'], 'y': 0}
        for d in datapoints if d['x'] is not None]


class Summarizer(object):
    def __init__(self, time_aligner, bucket_size):
        self.time_aligner = time_aligner
        self.bucket_size = bucket_size

    def align_time(self, t):
        return self.time_aligner(t, self.bucket_size)

    def __call__(self, from_time, datapoints):
        raise NotImplementedError()


class LastDatapointSummarizer(Summarizer):
    def __call__(self, from_time, datapoints):
        step = self.align_time(from_time)

        results = []
        if not datapoints:
            return results

        it = iter(datapoints)
        prev = next(it)
        for curr in it:
            aligned_x = self.align_time(curr['x'])
            if aligned_x > step:
                results.append({'x': step, 'y': prev['y']})
                step = aligned_x
            prev = curr

        # add the last datapoint
        results.append({
            'x': self.align_time(prev['x']),
            'y': prev['y']
        })

        return results


class AggregatingSummarizer(Summarizer):
    def __init__(self, aggregator, *args, **kwargs):
        super(AggregatingSummarizer, self).__init__(*args, **kwargs)
        self.aggregator = aggregator

    def __call__(self, from_time, datapoints):
        step = self.align_time(from_time)

        results = []
        if not datapoints:
            return results

        bucket = []
        for datapoint in datapoints:
            aligned_x = self.align_time(datapoint['x'])
            if aligned_x > step:
                if bucket:
                    results.append({'x': step, 'y': self.aggregator(bucket)})
                bucket = []
                step = aligned_x
            bucket.append(datapoint['y'])

        # add the aggregation result of the last bucket
        results.append({'x': step, 'y': self.aggregator(bucket)})

        return results


class Summarizers(object):
    OVERRIDES = {
        'last': LastDatapointSummarizer
    }

    @classmethod
    def get(cls, agg_method, time_alignment, bucket_size):
        time_aligner = utils.time_aligners.get(time_alignment)

        if agg_method in cls.OVERRIDES:
            summarizer_cls = cls.OVERRIDES[agg_method]
            return summarizer_cls(time_aligner, bucket_size)

        aggregator = aggregators.get(agg_method)
        return AggregatingSummarizer(aggregator, time_aligner, bucket_size)


aggregators = {
    'max': max,
    'min': min,
    'sum': sum,
    'avg': (lambda vals: sum(vals) / (len(vals) or 1)),
}


null_filters = {
    'skip': skip_nulls,
    'zeroize': zeroize_nulls,
}


summarizers = Summarizers()
