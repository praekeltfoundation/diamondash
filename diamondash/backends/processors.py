from diamondash import utils


def skip_nulls(datapoints):
    return [d for d in datapoints
            if d['y'] is not None and d['x'] is not None]


def zeroize_nulls(datapoints):
    return [d if d['y'] is not None else {'x': d['x'], 'y': 0}
            for d in datapoints if d['x'] is not None]


class Summarizer(object):
    def __init__(self, bucket_size, time_aligner=utils.round_time):
        self.bucket_size = bucket_size
        self.time_aligner = time_aligner

    def align_time(self, t):
        print t
        print self.bucket_size
        return self.time_aligner(t, self.bucket_size)

    def __call__(self, datapoints, from_time):
        raise NotImplementedError()


class LastDatapointSummarizer(Summarizer):
    def __call__(self, datapoints, from_time):
        step = self.align_time(from_time)
        pivot_size = self.bucket_size * 0.5
        pivot = step + pivot_size

        results = []
        if not datapoints:
            return results

        it = iter(datapoints)
        prev = next(it)
        for curr in it:
            if curr['x'] >= pivot:
                results.append({'x': step, 'y': prev['y']})
                step = self.align_time(curr['x'])
                pivot = step + pivot_size
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

    def __call__(self, datapoints, from_time):
        step = self.align_time(from_time)
        pivot_size = self.bucket_size * 0.5
        pivot = step + pivot_size

        results = []
        if not datapoints:
            return results

        bucket = []
        for datapoint in datapoints:
            if datapoint['x'] >= pivot:
                results.append({'x': step, 'y': self.aggregator(bucket)})
                bucket = []
                step = self.align_time(datapoint['x'])
                pivot = step + pivot_size
            bucket.append(datapoint['y'])

        # add the aggregation result of the last bucket
        results.append({'x': step, 'y': self.aggregator(bucket)})

        return results


get_null_filter = utils.Accessor(
    skip=skip_nulls,
    zeroize=zeroize_nulls,
    fallback=zeroize_nulls
)


avg = (lambda vals: sum(vals) / (len(vals) or 1))
get_aggregator = utils.Accessor(**{
    'max': max,
    'min': min,
    'sum': sum,
    'avg': avg,
    'fallback': avg,
})


get_summarizer = utils.Accessor(
    wrapper=lambda agg_method, fn, *a, **kw: fn(agg_method, *a, **kw),
    last=lambda agg_method, *a, **kw: LastDatapointSummarizer(*a, **kw),
    fallback=lambda agg_method, *a, **kw: (
        AggregatingSummarizer(get_aggregator(agg_method), *a, **kw))
)
