import re
import json
from urllib import urlencode
from urlparse import urljoin

from twisted.web import client
from twisted.python import log

from diamondash import utils
from diamondash.config import ConfigError
from diamondash.backends import (
    processors, BackendConfig, Backend, MetricConfig, Metric)


class GraphiteBackendConfig(BackendConfig):
    DEFAULTS = {
        'time_aligner': 'round'
    }

    METRIC_UNDERRIDES = [
        'bucket_size',
        'null_filter',
        'time_aligner',
    ]

    @classmethod
    def parse(cls, config):
        if 'url' not in config:
            raise ConfigError("GraphiteBackend needs a 'url' config field.")

        metric_underrides = dict(
            (k, config.pop(k))
            for k in cls.METRIC_UNDERRIDES if k in config)

        config['metrics'] = [
            utils.add_dicts(metric_underrides, m) for m in config['metrics']]

        config['metrics'] = [
            GraphiteMetricConfig(m) for m in config['metrics']]

        return config


class GraphiteBackend(Backend):
    CONFIG_CLS = GraphiteBackendConfig

    def __init__(self, config):
        super(GraphiteBackend, self).__init__(config)

        self.metrics = []
        self.metrics_by_target = {}

        for metric_config in self.config['metrics']:
            self.add_metric(metric_config)

    def build_request_params(self, **params):
        req_params = {}
        if 'from_time' in params:
            req_params['from'] = int(params['from_time'] / 1000)
        if 'until_time' in params:
            req_params['until'] = int(params['until_time'] / 1000)

        req_params.update({
            'format': 'json',
            'target': [m.aliased_target() for m in self.metrics]
        })
        return req_params

    def build_request_url(self, **params):
        req_params = self.build_request_params(**params)
        render_url = "render/?%s" % urlencode(req_params, True)
        return urljoin(self.config['url'], render_url)

    def add_metric(self, config):
        target = config['target']

        if target in self.metrics_by_target:
            log.msg("Metric with target '%s' already exists in "
                    "Graphite backend." % (target))
            return

        metric = GraphiteMetric(config)
        self.metrics.append(metric)
        self.metrics_by_target[target] = metric

    def handle_backend_response(self, data, **request_params):
        """
        Accepts graphite render response data and processes it into a
        normalized format.
        """
        data = json.loads(data)

        datapoints_by_target = dict(
            (metric['target'], metric['datapoints']) for metric in data)

        output = []
        for metric in self.metrics:
            datapoints = metric.process_datapoints(
                datapoints_by_target.get(metric.config['target'], []),
                **request_params)
            output.append({
                'id': metric.config['id'],
                'datapoints': datapoints,
            })

        return output

    def get_data(self, **params):
        if 'from_time' in params:
            params['from_time'] = utils.absolute_time(params['from_time'])

        if 'until_time' in params:
            params['until_time'] = utils.absolute_time(params['until_time'])

        request_url = self.build_request_url(**params)
        d = client.getPage(request_url)
        d.addCallback(self.handle_backend_response, **params)
        return d


class GraphiteMetricConfig(MetricConfig):
    DEFAULTS = {
        'null_filter': 'skip',
        'time_alignment': 'round',
    }

    @classmethod
    def parse(cls, config):
        config = super(GraphiteMetricConfig, cls).parse(config)

        config['bucket_size'] = utils.parse_interval(config['bucket_size'])

        config.setdefault(
            'agg_method',
            guess_aggregation_method(config['target']))

        return config


class GraphiteMetric(Metric):
    """A metric displayed by a GraphiteWidget"""

    CONFIG_CLS = GraphiteMetricConfig

    def __init__(self, config):
        super(GraphiteMetric, self).__init__(config)

        self.null_filter = processors.null_filters.get(
            self.config['null_filter'])

        self.summarizer = processors.summarizers.get(
            self.config['agg_method'],
            self.config['time_alignment'],
            self.config['bucket_size'])

    @staticmethod
    def alias_target(target):
        return "alias(%s, '%s')" % (target, target)

    def aliased_target(self):
        return self.alias_target(self.config['target'])

    def process_datapoints(self, datapoints, **params):
        """
        Takes in datapoints received from graphite, performs any processing
        that needs to be performed for a particular metric (eg. null
        filtering), and returns the processed datapoints.
        """
        # convert to internal format
        datapoints = [{'x': x * 1000, 'y': y} for y, x in datapoints]
        datapoints = self.null_filter(datapoints)

        if 'from_time' in params:
            datapoints = self.summarizer(params['from_time'], datapoints)

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
            if suffix in ('min', 'max', 'avg', 'sum', 'last'):
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
