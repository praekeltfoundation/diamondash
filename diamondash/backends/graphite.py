import re
import json
from urllib import urlencode

from twisted.web import client
from twisted.python import log

from diamondash import utils, ConfigMixin, ConfigError
from diamondash.backends import Backend


class GraphiteBackend(Backend):
    """Abstract widget for displaying metric data from graphite."""

    __DEFAULTS = {
        'graphite_url': 'http://127.0.0.1:8080',
        'from_time': '1d',
    }
    __CONFIG_TAG = 'diamondash.backends.graphite.GraphiteBackend'

    def __init__(self, graphite_url, from_time, metrics=[]):
        self.graphite_url = graphite_url
        self.from_time = from_time

        self.metrics = []
        self.metrics_by_target = {}
        self.add_metrics(metrics)

    @classmethod
    def parse_config(cls, config, class_defaults={}):
        config = super(GraphiteBackend, cls).parse_config(
            config, class_defaults)
        defaults = class_defaults.get(cls.__CONFIG_TAG, {})
        config = utils.update_dict(config, cls.__DEFAULTS, defaults)

        config['from_time'] = utils.parse_interval(config['from_time'])
        config['metrics'] = [GraphiteMetric.from_config(m, class_defaults)
                             for m in config.get('metrics', [])]

        return config

    @classmethod
    def build_request_url(cls, graphite_url, from_time, targets):
        """
        Constructs the graphite render url
        """
        params = [
            ('from', "-%ss" % from_time),
            ('target', targets),
            ('format', 'json')]
        render_url = "render/?%s" % urlencode(params, True)
        return '/'.join((graphite_url.strip('/'), render_url))

    def _build_request_url(self, graphite_url, from_time):
        """
        Internal method that constructs the graphite request url using the
        calling instance's metrics' wrapped targets.
        """
        wrapped_targets = [m.wrapped_target for m in self.metrics]
        return self.build_request_url(graphite_url, from_time, wrapped_targets)

    def _reset_request_url(self):
        self.request_url = self._build_request_url(
            self.graphite_url, self.from_time)

    def _add_metric(self, metric):
        """
        Adds a metric to the widget. Used by `add_metric()` and `add_metrics()`
        to keep things DRY.
        """
        target = metric.target
        if target in self.metrics_by_target:
            log.msg("Metric with target '%s' already exists in "
                    "Graphite backend." % target)
            return

        self.metrics.append(metric)
        self.metrics_by_target[target] = metric

    def add_metric(self, metric):
        """
        Adds a single metric to the widget and rebuilds the request url.
        """
        self._add_metric(metric)
        self._reset_request_url()

    def add_metrics(self, metrics):
        """
        Adds a multiple metrics to the widget and rebuilds the request url.
        """
        for metric in metrics:
            self._add_metric(metric)
        self._reset_request_url()

    def handle_graphite_response(self, data):
        """
        Accepts graphite render response data and processes it into a
        normalized format.
        """
        data = json.loads(data)

        datapoints_by_target = dict(
            (metric['target'], metric['datapoints']) for metric in data)

        output = []
        for metric in self.metrics:
            datapoints = datapoints_by_target.get(metric.target, [])
            if datapoints:
                datapoints = metric.process_datapoints(datapoints)
            output.append({
                'datapoints': datapoints,
                'metadata': metric.metadata
            })

        return output

    def get_data(self, **kwargs):
        if not kwargs:
            request_url = self.request_url
        else:
            graphite_url = kwargs.get('graphite_url', self.graphite_url)
            from_time = kwargs.get('from_time', self.from_time)
            from_time = utils.parse_interval(from_time)
            request_url = self._build_request_url(graphite_url, from_time)

        d = client.getPage(request_url)
        d.addCallback(self.handle_graphite_response)
        return d


class GraphiteMetric(ConfigMixin):
    """A metric displayed by a GraphiteWidget"""

    __DEFAULTS = {'null_filter': 'skip'}
    __CONFIG_TAG = 'diamondash.backends.graphite.GraphiteMetric'

    def __init__(self, target, wrapped_target, null_filter, metadata):
        self.target = target
        self.wrapped_target = wrapped_target
        self.set_null_filter(null_filter)
        self.metadata = metadata

    def set_null_filter(self, filter_name):
        self.filter_nulls = {
            'skip': self.skip_nulls,
            'zeroize': self.zeroize_nulls,
            'noop': lambda x: x
        }.get(filter_name, self.skip_nulls)

    @classmethod
    def skip_nulls(cls, datapoints):
        return [[y, x] for [y, x] in datapoints
                if (y is not None) and (x is not None)]

    @classmethod
    def zeroize_nulls(cls, datapoints):
        return [[y, x] if y is not None else [0, x]
                for [y, x] in datapoints if x is not None]

    @classmethod
    def parse_config(cls, config, class_defaults={}):
        defaults = class_defaults.get(cls.__CONFIG_TAG, {})
        config = utils.update_dict(config, cls.__DEFAULTS, defaults)

        target = config.get('target')
        if target is None:
            raise ConfigError("All metrics need a target")

        bucket_size = config.pop('bucket_size', None)
        if bucket_size is not None:
            bucket_size = utils.parse_interval(bucket_size)
            config['wrapped_target'] = cls.format_metric_target(
                target, bucket_size)
        else:
            config['wrapped_target'] = target

        config.setdefault('metadata', {})

        return config

    @classmethod
    def format_metric_target(cls, target, bucket_size):
        """
        Formats a metric target to allow aggregation of metric values
        based on the passed in bucket size
        """
        bucket_size = '%ss' % (str(bucket_size),)
        agg_method = guess_aggregation_method(target)
        if agg_method is None:
            # TODO: Log this?
            agg_method = "avg"

        graphite_target = 'alias(summarize(%s, "%s", "%s"), "%s")' % (
            target, bucket_size, agg_method, target)

        return graphite_target

    def process_datapoints(self, datapoints):
        """
        Takes in datapoints received from graphite, performs any processing
        that needs to be performed for a particular metric (eg. null
        filtering), and returns the processed datapoints.
        """
        datapoints = self.filter_nulls(datapoints)
        return [{'x': x, 'y': y} for y, x in datapoints]


# Borrowed from the bit of pyparsing, the graphite expression parser uses.
_quoted_string_re = re.compile(
    r'''(?:"(?:[^"\n\r\\]|(?:"")|(?:\\x[0-9a-fA-F]+)|(?:\\.))*")|'''
    r'''(?:'(?:[^'\n\r\\]|(?:'')|(?:\\x[0-9a-fA-F]+)|(?:\\.))*')''')


def lex_graphite_expression(expression):
    tokens = []

    while expression:
        if expression[0] == ')':
            tokens.append(('endfunc', ''))
            expression = expression[1:].strip().strip(',').strip()
            continue
        match = _quoted_string_re.match(expression)
        if match:
            # Throw away the string
            expression = expression[match.end():].strip().strip(',').strip()
            continue

        token, new_expression = (expression.split(',', 1) + [''])[:2]
        if '(' in token:
            token, new_expression = expression.split('(', 1)
            tokens.append(('func', token.strip()))
        elif ')' in token:
            token, new_expression = expression.split(')', 1)
            tokens.append(('item', token.strip()))
            new_expression = ')' + new_expression
        else:
            tokens.append(('item', token.strip()))
        expression = new_expression.strip()
    return tokens


def parse_graphite_func(tokens):
    results = []
    while tokens:
        token, value = tokens.pop(0)
        if token == 'endfunc':
            return ([r for r in results if r is not None] + [None])[0]
        elif token == 'func':
            if value == 'integral':
                # Special case.
                results.append('max')
            results.append(parse_graphite_func(tokens))
        elif token == 'item':
            suffix = value.split('.')[-1]
            if suffix in ('min', 'max', 'avg', 'sum'):
                results.append(suffix)


def guess_aggregation_method(target):
    """
    Guess aggregation method for a particular metric.

    The result is based on a depth-first search of nested functions for
    things that look like metric names with suitable aggregation suffixes.
    All functions are "evaluated" to the aggregation type of the first param
    that has one. If nothing suitable is found, `None` is returned.

    The "integral()" function is treated as a special case and given an
    aggregation method of "max".
    """

    tokens = lex_graphite_expression(target)
    return parse_graphite_func(tokens + [('endfunc', '')])
