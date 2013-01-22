import re
import json
from urllib import urlencode

from twisted.web import client

from diamondash import utils
from diamondash.widgets.widget import Widget
from diamondash.exceptions import ConfigError


class GraphiteWidget(Widget):
    """Abstract widget for displaying metric data from graphite."""

    DEFAULTS = {'graphite_url': 'http://127.0.0.1:8080'}

    def __init__(self, **kwargs):
        super(GraphiteWidget, self).__init__(**kwargs)
        self.from_time = kwargs['from_time']
        self.bucket_size = kwargs['bucket_size']
        self.graphite_url = kwargs['graphite_url']

    @classmethod
    def parse_config(cls, config, defaults={}):
        """Parses the graphite widget config, altering it where necessary."""
        config = super(GraphiteWidget, cls).parse_config(config, defaults)

        config = dict(cls.DEFAULTS, **config)
        config = utils.set_key_defaults(
            'diamondash.widgets.graphite.GraphiteWidget', config, defaults)

        if 'graphite_url' not in config:
            raise ConfigError(
                "Graphite widget %s needs a graphite_url" % config['name'])

        return config

    @classmethod
    def build_request_url(cls, graphite_url, targets, from_param):
        """
        Constructs the graphite render url
        """
        params = {
            'target': targets,
            'from': "-%ss" % from_param,
            'format': 'json',
        }
        render_url = "render/?%s" % urlencode(params, True)
        graphite_url = graphite_url.strip('/')

        return '/'.join((graphite_url, render_url))

    def _reset_request_url(self):
        """
        Resets an instance's request_url (due to changes to the graphite url,
        metric(s), or request parameters.

        NOTE: To be implemented by subclasses.
        """
        pass

    def handle_graphite_render_response(self, data):
        """
        Accepts graphite render response data and performs any necessary
        data processing/formatting/mangling steps to have the data useable by
        the client side.

        To be implemented by subclasses.
        """
        return data

    def handle_render_request(self, request):
        if self.request_url is None:
            # TODO: log?
            return "{}"

        d = client.getPage(self.request_url)
        d.addCallback(lambda data: json.loads(data))
        d.addCallback(self.handle_graphite_render_response)

        return d


class SingleMetricGraphiteWidget(GraphiteWidget):
    """Abstract widget for displaying a single metric's data from graphite."""

    def __init__(self, **kwargs):
        super(SingleMetricGraphiteWidget, self).__init__(**kwargs)
        self.set_metric(kwargs['metric'])

    def _reset_request_url(self):
        self.request_url = self.build_request_url(
            self.graphite_url, [self.metric.wrapped_target], self.from_time)

    def set_metric(self, metric):
        """Sets the widget's metric"""
        self.metric = metric
        self._reset_request_url()

    def handle_graphite_render_response(self, data):
        """
        Accepts graphite render response data and performs the data processing
        and formatting on the datapoints based on the widget's metric's
        configuration.
        """
        metric_data = utils.find_dict_by_item(
            data, 'target', self.metric.target)

        if metric_data is None:
            # TODO: log?
            return "{}"

        return self.metric.process_datapoints(metric_data['datapoints'])


class MultiMetricGraphiteWidget(GraphiteWidget):
    """
    Abstract widget for displaying a multiple metrics' data from graphite.
    """

    def __init__(self, **kwargs):
        super(MultiMetricGraphiteWidget, self).__init__(**kwargs)
        self.metrics = []
        self.metrics_by_target = {}

        for metric in kwargs['metrics']:
            self.add_metric(metric)

    def _reset_request_url(self):
        wrapped_targets = [m.wrapped_target for m in self.metrics]
        self.request_url = self.build_request_url(
            self.graphite_url, wrapped_targets, self.from_time)

    def _add_metric(self, metric):
        """
        Adds a metric to the widget. Used by `add_metric()` and `add_metrics()`
        to keep things DRY.
        """
        self.metrics.append(metric)
        self.metrics_by_target[metric.target] = metric

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

    def handle_graphite_render_response(self, data):
        """
        Accepts graphite render response data and performs the data processing
        and formatting on the datapoints based on the widget's metrics'
        configurations.
        """
        datapoints_by_target = {}
        for metric_data in data:
            target = metric_data['target']
            metric = self.metrics_by_target.get(target, None)
            if metric is not None:
                datapoints_by_target[target] = metric.process_datapoints(
                    metric_data['datapoints'])

        for k in self.metrics_by_target.keys():
            datapoints_by_target.setdefault(k, [])

        return datapoints_by_target


class GraphiteWidgetMetric(object):
    """A metric displayed by a GraphiteWidget"""

    DEFAULTS = {'null_filter': 'skip'}

    def __init__(self, **kwargs):
        self.target = kwargs['target']
        self.wrapped_target = kwargs['wrapped_target']
        self.set_null_filter(kwargs['null_filter'])

    @classmethod
    def skip_nulls(cls, datapoints):
        return [[y, x] for [y, x] in datapoints
                if (y is not None) and (x is not None)]

    @classmethod
    def zeroize_nulls(cls, datapoints):
        return [[y, x] if y is not None else [0, x]
                for [y, x] in datapoints if x is not None]

    def set_null_filter(self, filter_name):
        self.filter_nulls = {
            'skip': self.skip_nulls,
            'zeroize': self.zeroize_nulls,
            'noop': lambda x: x
        }.get(filter_name, self.skip_nulls)

    @classmethod
    def parse_config(cls, config, defaults={}):
        defaults = dict(cls.DEFAULTS, **defaults)
        config = dict(defaults, **config)

        target = config.get('target', None)
        if target is None:
            raise ConfigError("All metrics need a target")

        bucket_size = config.get('bucket_size', None)
        if bucket_size is not None:
            bucket_size = utils.parse_interval(bucket_size)
            config['bucket_size'] = bucket_size
            config['wrapped_target'] = cls.format_metric_target(
                target, bucket_size)
        else:
            config['wrapped_target'] = target

        return config

    @classmethod
    def from_config(cls, config, defaults={}):
        config = cls.parse_config(config, defaults)
        return cls(**config)

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

        return datapoints


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
