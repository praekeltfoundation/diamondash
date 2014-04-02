from functools import partial

from diamondash import utils


def skip_nulls(datapoints):
    return [
        d for d in datapoints
        if d['y'] is not None and d['x'] is not None]


def zeroize_nulls(datapoints):
    return [
        d if d['y'] is not None else {'x': d['x'], 'y': 0}
        for d in datapoints if d['x'] is not None]


def agg_max(vals):
    return max(vals) if vals else 0


def agg_min(vals):
    return min(vals) if vals else 0


def agg_avg(vals):
    return sum(vals) / len(vals) if vals else 0


class Summarizer(object):
    def __init__(self, time_aligner, bucket_size, relative=False):
        self.relative = relative
        self.time_aligner = time_aligner
        self.bucket_size = bucket_size

    def align_time(self, t, from_time):
        relative_to = from_time if self.relative else None
        return self.time_aligner(t, self.bucket_size, relative_to=relative_to)

    def __call__(self, from_time, datapoints):
        raise NotImplementedError()


class LastDatapointSummarizer(Summarizer):
    def __call__(self, from_time, datapoints):
        step = self.align_time(from_time, from_time)

        results = []
        if not datapoints:
            return results

        it = iter(datapoints)
        prev = next(it)
        for curr in it:
            aligned_x = self.align_time(curr['x'], from_time)
            if aligned_x > step:
                results.append({'x': step, 'y': prev['y']})
                step = aligned_x
            prev = curr

        # add the last datapoint
        results.append({
            'x': self.align_time(prev['x'], from_time),
            'y': prev['y']
        })

        return results


class AggregatingSummarizer(Summarizer):
    def __init__(self, time_aligner, bucket_size, aggregator, relative=False):
        super(AggregatingSummarizer, self).__init__(
            time_aligner, bucket_size, relative)
        self.aggregator = aggregator

    def __call__(self, from_time, datapoints):
        step = self.align_time(from_time, from_time)

        results = []
        if not datapoints:
            return results

        bucket = []
        for datapoint in datapoints:
            aligned_x = self.align_time(datapoint['x'], from_time)
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
    def __init__(self, summarizers):
        self.summarizers = summarizers

    def get(self, name, time_alignment, bucket_size, relative=False):
        time_aligner = utils.time_aligners.get(time_alignment)

        if name not in self.summarizers:
            raise KeyError("No summarizer called '%s' exists" % name)

        summarizer_cls = self.summarizers[name]
        return summarizer_cls(time_aligner, bucket_size, relative=relative)


null_filters = {
    'skip': skip_nulls,
    'zeroize': zeroize_nulls,
}

aggregators = {
    'sum': sum,
    'max': agg_max,
    'min': agg_min,
    'avg': agg_avg,
}

summarizers = Summarizers({
    'sum': partial(AggregatingSummarizer, aggregator=aggregators['sum']),
    'max': partial(AggregatingSummarizer, aggregator=aggregators['max']),
    'min': partial(AggregatingSummarizer, aggregator=aggregators['min']),
    'avg': partial(AggregatingSummarizer, aggregator=aggregators['avg']),
    'last': LastDatapointSummarizer,
})
