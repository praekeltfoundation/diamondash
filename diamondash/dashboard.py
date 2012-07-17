"""Dashboard functionality for the diamondash web app"""

import re
import json
from urllib import urlencode

import yaml
from unidecode import unidecode
from pkg_resources import resource_stream
from twisted.web.template import Element, renderer, XMLFile

from exceptions import ConfigError


# graph widget defaults
GRAPH_DEFAULTS = {
    'null_filter': 'skip',
    'time_range': 3600,
    'bucket_size': 300,
}


# lvalue widget defaults
LVALUE_DEFAULTS = {
    'time_range': 3600,
}


# dashboard defaults
DASHBOARD_DEFAULTS = {
    'request_interval': 2,
    'default_widget_type': 'graph',
}


def parse_interval(interval):
    """
    Recognise 's', 'm', 'h', 'd' suffixes as seconds, minutes, hours and days.
    Return integer seconds.
    """
    if not isinstance(interval, basestring):
        # It isn't a string, so there's nothing to parse
        return interval
    suffixes = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
    }
    try:
        for suffix, multiplier in suffixes.items():
            if interval.endswith(suffix):
                return int(interval[:-1]) * multiplier
        return int(interval)
    except ValueError:
        raise ConfigError("%r is not a valid time interval.")


def format_metric_target(target, bucket_size):
    """
    Formats a metric target to allow aggregation of metric values
    based on the passed in bucket size
    """
    bucket_size = '%ss' % (str(bucket_size),)
    agg_method = "avg"
    metric_fn = target.rstrip(')').split('.')[-1]
    if target.startswith('integral('):
        agg_method = 'max'
    elif metric_fn in ('max', 'min', 'sum'):
        agg_method = metric_fn
    return 'summarize(%s, "%s", "%s")' % (target, bucket_size, agg_method)


def build_request_url(targets, from_param):
    """
    Constructs the graphite render url
    """
    params = {'target': targets,
        'from': '-%ss' % from_param,
        'format': 'json'
    }
    return 'render/?%s' % urlencode(params, True)


def parse_graph_config(config, defaults):
    """
    Parses a graph widget's config, applying changes
    where appropriate and returning the resulting config
    """
    for field, default in defaults.items():
        config.setdefault(field, default)

    for field in ['time_range', 'bucket_size']:
        config[field] = parse_interval(config[field])

    metric_dict = {}
    bucket_size = config['bucket_size']
    for m_name, m_config in config['metrics'].items():
        if 'target' not in m_config:
            raise ConfigError(
                'Widget "%s" needs a target for metric "%s".'
                % (config['name'], m_name))

        m_config['original_target'] = m_config['target']
        m_config['target'] = format_metric_target(
            m_config['target'], bucket_size)
        m_config.setdefault('null_filter', config['null_filter'])

        for threshold in ['warning_min_threshold', 'warning_max_threshold']:
            if threshold in m_config:
                m_config[threshold] = int(m_config[threshold])

        m_config.setdefault('title', m_name)
        m_name = slugify(m_name)
        metric_dict[m_name] = m_config

    config['metrics'] = metric_dict

    targets = [metric['target'] for metric in metric_dict.values()]
    config['request_url'] = build_request_url(targets, config['time_range'])

    return config


def parse_lvalue_config(config, defaults):
    """
    Parses an lvalue widget's config, applying changes
    where appropriate and returning the resulting config
    """
    for field, default in defaults.items():
        config.setdefault(field, default)

    config['time_range'] = parse_interval(config['time_range'])

    metric_list = []
    for target in config['metrics']:
        m_config = {}
        m_config['original_target'] = target

        # Set the bucket size to the passed in time range
        # (for eg, if 1d was the time range, the data for the
        # entire day will be aggregated).
        m_config['target'] = format_metric_target(
            target, config['time_range'])

        metric_list.append(m_config)

    config['metrics'] = metric_list

    targets = [metric['target'] for metric in metric_list]

    # Set the from param to double the bucket size. As a result, graphite will
    # return two datapoints for each metric: the previous value and the last
    # value. The last and previous values will be used to calculate the
    # percentage increase.
    from_param = int(config['time_range']) * 2

    config['request_url'] = build_request_url(targets, from_param)

    return config


def parse_config(config):
    """
    Parses a dashboard config, applying changes
    where appropriate and returning the resulting config
    """
    config = dict(DASHBOARD_DEFAULTS, **config)

    if 'name' not in config:
        raise ConfigError('Dashboard name not specified.')

    config['title'] = config['name']
    config['name'] = slugify(config['name'])

    graph_defaults = config.setdefault('graph_defaults', {})
    for field, default in GRAPH_DEFAULTS.items():
        graph_defaults.setdefault(field, default)

    lvalue_defaults = config.setdefault('lvalue_defaults', {})
    for field, default in LVALUE_DEFAULTS.items():
        lvalue_defaults.setdefault(field, default)

    config['request_interval'] = parse_interval(config['request_interval'])

    widget_dict = {}
    widget_list = []
    for w_config in config['widgets']:
        if 'name' not in w_config:
            raise ConfigError('All widgets need a name')
        w_name = w_config['name']

        if 'metrics' not in w_config:
            raise ConfigError('Widget "%s" needs metric(s).' % (w_name,))

        w_config.setdefault('title', w_name)
        w_name = slugify(w_name)
        w_config['name'] = w_name

        w_config.setdefault('type', config['default_widget_type'])

        if w_config['type'] == 'graph':
            parse_widget_config = parse_graph_config
            widget_defaults = graph_defaults
        elif w_config['type'] == 'lvalue':
            parse_widget_config = parse_lvalue_config
            widget_defaults = lvalue_defaults

        w_config = parse_widget_config(w_config, widget_defaults)
        widget_dict[w_name] = w_config
        widget_list.append(w_config)

    # update widget dict
    config['widget_list'] = widget_list
    config['widgets'] = widget_dict

    return config


# metric attributes needed by client
CLIENT_GRAPH_METRIC_ATTRS = ['title', 'color', 'warning_max_threshold',
                      'warning_min_threshold', 'warning_color']


def build_client_config(server_config):
    """
    Builds a client side dashboard config from the server's
    dashboard config and returns it in JSON format
    """
    config = {}
    config['name'] = server_config['name']

    # convert the request interval to milliseconds for client side
    config['request_interval'] = int(server_config['request_interval']) * 1000

    w_configs = config.setdefault('widgets', {})
    for w_name, w_server_config in server_config['widgets'].items():
        w_configs[w_name] = {}

        # Add metric attributes for graph widgets
        if w_server_config['type'] == 'graph':
            m_configs = w_configs[w_name].setdefault('metrics', {})
            for m_name, m_server_config in w_server_config['metrics'].items():
                attrs = dict((k, m_server_config[k])
                             for k in CLIENT_GRAPH_METRIC_ATTRS
                             if k in m_server_config)
                m_configs[m_name] = attrs

    #serialize client vars into a json string ready for javascript
    return 'var config = %s;' % (json.dumps(config),)


class Dashboard(Element):
    """Dashboard element for the diamondash web app"""

    loader = XMLFile(resource_stream(__name__, 'templates/dashboard.xml'))

    def __init__(self, config):
        self.config = parse_config(config)
        self.client_config = build_client_config(self.config)

    @classmethod
    def from_config_file(cls, filename, defaults=None):
        """Loads dashboard config from a config file"""
        # TODO check and test for invalid config files

        config = {}
        if defaults is not None:
            config.update(defaults)

        try:
            config.update(yaml.safe_load(open(filename)))
        except IOError:
            raise ConfigError('File %s not found.' % (filename,))

        return cls(config)

    @classmethod
    def from_args(cls, **kwargs):
        """Loads dashboard config from args"""

        config = {}
        if kwargs is not None:
            config.update(kwargs)

        return cls(kwargs)

    def get_widget_config(self, w_name):
        """Returns a widget using the passed in widget name"""
        return self.config['widgets'][w_name]

    @renderer
    def widget_renderer(self, request, tag):
        for w_config in self.config['widget_list']:
            new_tag = tag.clone()

            class_attr_list = ['span4', 'widget', '%s-widget'
                               % (w_config['type'],)]
            class_attr = ' '.join('%s' % attr for attr in class_attr_list)

            # to not break the template with invalid types
            widget_element = ''

            Widget = {
                'graph': GraphWidget,
                'lvalue': LValueWidget,
            }.get(w_config['type'], GraphWidget)
            widget_element = Widget()

            new_tag.fillSlots(widget_title_slot=w_config['title'],
                              widget_class_slot=class_attr,
                              widget_id_slot=w_config['name'],
                              widget_element_slot=widget_element)
            yield new_tag

    @renderer
    def config_script(self, request, tag):
        if self.client_config is not None:
            tag.fillSlots(client_config=self.client_config)
            return tag


class GraphWidget(Element):
    """Graph element that resides in a Dashboard element"""

    loader = XMLFile(resource_stream(__name__, 'templates/graph_widget.xml'))


class LValueWidget(Element):
    """LValue element that resides in a Dashboard element"""

    loader = XMLFile(resource_stream(__name__, 'templates/lvalue_widget.xml'))


_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text):
    """Slugifies the passed in text"""
    result = []
    for word in _punct_re.split(text.lower()):
        result.extend(unidecode(word).split())
    return '-'.join(result)
