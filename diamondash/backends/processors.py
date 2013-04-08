from diamondash import utils


def skip_nulls(datapoints):
    return [d for d in datapoints
            if d['y'] is not None and d['x'] is not None]


def zeroize_nulls(datapoints):
    return [d if d['y'] is not None else {'x': d['x'], 'y': 0}
            for d in datapoints if d['x'] is not None]


class Summarizer(object):
    def __init__(self, bucket_size):
        self.bucket_size = bucket_size

    def __call__(self, datapoints, from_time):
        raise NotImplementedError()


class LastDatapointSummarizer(Summarizer):
    def __call__(self, datapoints, from_time):
        step = utils.round_time(from_time, self.bucket_size)
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
                step = utils.round_time(curr['x'], self.bucket_size)
                pivot = step + pivot_size
            prev = curr

        # add the last datapoint
        results.append({
            'x': utils.round_time(prev['x'], self.bucket_size),
            'y': prev['y']
        })

        return results


class AggregatingSummarizer(Summarizer):
    def __init__(self, bucket_size, aggregator):
        self.bucket_size = bucket_size
        self.aggregator = aggregator

    def __call__(self, datapoints, from_time):
        step = utils.round_time(from_time, self.bucket_size)
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
                step = utils.round_time(datapoint['x'], self.bucket_size)
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
    wrapper=lambda agg_method, fn, bucket_size: fn(bucket_size, agg_method),
    last=lambda bucket_size, agg_method: LastDatapointSummarizer(bucket_size),
    fallback=lambda bucket_size, agg_method: (
        AggregatingSummarizer(bucket_size, get_aggregator(agg_method)))
)
