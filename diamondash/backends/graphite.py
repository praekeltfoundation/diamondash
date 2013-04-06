import re
import json
from urllib import urlencode
from urlparse import urljoin

from twisted.web import client
from twisted.python import log

from diamondash import utils, ConfigMixin, ConfigError
from diamondash.backends import Backend
from diamondash.backends.processors import get_null_filter, get_summarizer


class GraphiteBackend(Backend):
    """Abstract widget for displaying metric data from graphite."""

    __DEFAULTS = {}
    __CONFIG_TAG = 'diamondash.backends.graphite.GraphiteBackend'

    # Using this for three reasons:
    # 1. Params such as 'from' are reserved words.
    # 2. Eventually, if and when we support multiple backends, we will need a
    # standard set of param names that can be converted to the param names
    # needed in requests to a particular backend.
    # 3. Allows params not supported by the backend to be excluded.
    REQUEST_PARAMS_MAP = {
        'from_time': 'from',
        'until_time': 'until',
    }

    def __init__(self, graphite_url, metrics=[]):
        self.graphite_url = graphite_url

        self.metrics = []
        self.metrics_by_target = {}
        for metric in metrics:
            self.add_metric(metric)

    @classmethod
    def parse_config(cls, config, class_defaults={}):
        config = super(GraphiteBackend, cls).parse_config(
            config, class_defaults)
        defaults = class_defaults.get(cls.__CONFIG_TAG, {})
        config = utils.update_dict(cls.__DEFAULTS, defaults, config)

        if 'graphite_url' not in config:
            raise ConfigError(
                "GraphiteBackend needs a 'graphite_url' config field.")

        metrics = config.get('metrics', [])
        if 'bucket_size' in config:
            bucket_size = config.pop('bucket_size')
            for m in metrics:
                m['bucket_size'] = bucket_size

        config['metrics'] = [GraphiteMetric.from_config(m, class_defaults)
                             for m in metrics]

        return config

    def build_request_params(self, **params):
        req_params = dict((req_k, params[k])
            for k, req_k in self.REQUEST_PARAMS_MAP.iteritems() if k in params)
        req_params.update({
            'format': 'json',
            'target': [m.wrapped_target for m in self.metrics]
        })
        return req_params

    def build_request_url(self, **params):
        req_params = self.build_request_params(**params)
        render_url = "render/?%s" % urlencode(req_params, True)
        return urljoin(self.graphite_url, render_url)

    def add_metric(self, metric):
        target = metric.target
        if target in self.metrics_by_target:
            log.msg("Metric with target '%s' already exists in "
                    "Graphite backend." % (target))
            return

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
                datapoints_by_target.get(metric.target, []),
                **request_params)
            output.append({
                'datapoints': datapoints,
                'metadata': metric.metadata
            })

        return output

    @staticmethod
    def parse_time(t):
        return utils.relative_to_now(t) if t < 0 else t

    def get_data(self, **params):
        if 'from_time' in params:
            params['from_time'] = self.parse_time(params['from_time'])

        if 'until_time' in params:
            params['until_time'] = self.parse_time(params['until_time'])

        request_url = self.build_request_url(**params)
        d = client.getPage(request_url)
        d.addCallback(self.handle_backend_response, **params)
        return d


class GraphiteMetric(ConfigMixin):
    """A metric displayed by a GraphiteWidget"""

    __DEFAULTS = {'null_filter': 'skip'}
    __CONFIG_TAG = 'diamondash.backends.graphite.GraphiteMetric'

    def __init__(self, target, metadata={}, null_filter=None, summarizer=None):
        self.target = target
        self.wrapped_target = self.alias_target(target)
        self.metadata = metadata
        self.null_filter = null_filter or get_null_filter('fallback')
        self.summarizer = summarizer or get_summarizer('fallback')

    @classmethod
    def parse_config(cls, config, class_defaults={}):
        defaults = class_defaults.get(cls.__CONFIG_TAG, {})
        config = utils.update_dict(cls.__DEFAULTS, defaults, config)

        if 'target' not in config:
            raise ConfigError("All metrics need a target")

        if 'bucket_size' in config:
            bucket_size = utils.parse_interval(config.pop('bucket_size'))
            agg_method = guess_aggregation_method(config['target'])
            config['summarizer'] = get_summarizer(agg_method, bucket_size)

        if 'null_filter' in config:
            config['null_filter'] = get_null_filter(config['null_filter'])

        return config

    @staticmethod
    def alias_target(target):
        return "alias(%s, '%s')" % (target, target)

    def process_datapoints(self, datapoints, **params):
        """
        Takes in datapoints received from graphite, performs any processing
        that needs to be performed for a particular metric (eg. null
        filtering), and returns the processed datapoints.
        """
        # convert to internal format
        datapoints = [{'x': x, 'y': y} for y, x in datapoints]
        datapoints = self.null_filter(datapoints)

        if 'from_time' in params:
            datapoints = self.summarizer(datapoints, params['from_time'])

        # convert x values to milliseconds for client
        for datapoint in datapoints:
            datapoint['x'] = utils.to_client_interval(datapoint['x'])

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
