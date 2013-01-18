import re
import json
from urllib import urlencode

from twisted.web import client

from diamondash import utils
from diamondash.widgets.widget import Widget
from diamondash.exceptions import ConfigError


class GraphiteWidget(Widget):
    """Abstract widget that obtains metric data from graphite."""

    def __init__(self, **kwargs):
        super(GraphiteWidget, self).__init__(**kwargs)
        self.request_url = kwargs['request_url']

    @classmethod
    def parse_config(cls, config, defaults={}):
        """Parses the graphite widget config, altering it where necessary."""
        config = super(GraphiteWidget, cls).parse_config(config, defaults)
        print defaults
        config = utils.insert_defaults_by_key(
            'diamondash.widgets.graphite.GraphiteWidget', config, defaults)

        if 'graphite_url' not in config:
            raise ConfigError(
                "Graphite widget %s needs a graphite_url" % config['name'])

        # NOTE: Must be built in subclasses
        config['request_url'] = None

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
