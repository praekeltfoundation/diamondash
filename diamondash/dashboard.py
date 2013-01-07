"""Dashboard functionality for the diamondash web app"""

import re
import json
from os import listdir, path
from urllib import urlencode

import yaml
from unidecode import unidecode
from pkg_resources import resource_string
from twisted.web.template import Element, renderer, XMLString

from exceptions import ConfigError

# graph widget defaults
GRAPH_DEFAULTS = {
    'null_filter': 'skip',
    'time_range': 3600,
    'bucket_size': 300,
    'width': 1,
}


# lvalue widget defaults
LVALUE_DEFAULTS = {
    'time_range': 3600,
}


LVALUE_GROUP_CAPACITY = 3


MIN_COLUMN_SPAN = 1
MAX_COLUMN_SPAN = 3


LAYOUT_RESERVED_WORDS = ['newrow', 'newcol']


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


def parse_graph_width(width):
    """
    Wraps the passed in width as an int and
    clamps the value to the width range
    """
    width = int(width)
    width = max(MIN_COLUMN_SPAN, min(width, MAX_COLUMN_SPAN))
    return width


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

    key = 'summarize(%s, "%s")' % (target, bucket_size)
    target = 'summarize(%s, "%s", "%s")' % (target, bucket_size, agg_method)
    return key, target


def build_request_url(targets, from_param):
    """
    Constructs the graphite render url
    """
    params = {
        'target': targets,
        'from': '-%ss' % from_param,
        'format': 'json',
    }
    return 'render/?%s' % urlencode(params, True)


def parse_graph_config(config, defaults):
    """
    Parses a graph widget's config, applying changes
    where appropriate and returning the resulting config
    """
    w_name = config['name']

    for field, default in defaults.items():
        config.setdefault(field, default)

    for field in ['time_range', 'bucket_size']:
        config[field] = parse_interval(config[field])

    config['width'] = parse_graph_width(config['width'])

    target_keys = []
    metric_list = []
    bucket_size = config['bucket_size']
    for m_config in config['metrics']:
        m_name = m_config.get('name', None)
        if m_name is None:
            raise ConfigError('Widget "%s" needs a name for all its metrics.'
                              % w_name)

        original_target = m_config.get('target', None)
        if original_target is None:
            raise ConfigError('Widget "%s" needs a target for metric "%s".'
                              % (w_name, m_name))

        original_target = m_config['target']
        m_config['original_target'] = original_target
        target_key, target = format_metric_target(original_target, bucket_size)
        target_keys.append(target_key)
        m_config['target'] = target

        m_config.setdefault('null_filter', config['null_filter'])

        for threshold in ['warning_min_threshold', 'warning_max_threshold']:
            if threshold in m_config:
                m_config[threshold] = int(m_config[threshold])

        m_config.setdefault('title', m_name)
        m_config['name'] = slugify(m_name)
        metric_list.append(m_config)

    config['metrics'] = metric_list
    config['target_keys'] = target_keys
    targets = [metric['target'] for metric in metric_list]
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

    target_keys = []
    metric_list = []
    for target in config['metrics']:
        m_config = {}
        m_config['original_target'] = target

        # Set the bucket size to the passed in time range
        # (for eg, if 1d was the time range, the data for the
        # entire day will be aggregated).
        bucket_size = config['time_range']

        target_key, target = format_metric_target(target, bucket_size)
        m_config['target'] = target
        target_keys.append(target_key)
        metric_list.append(m_config)

    config['metrics'] = metric_list
    targets = [metric['target'] for metric in metric_list]
    config['target_keys'] = target_keys

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
        if (isinstance(w_config, str) and w_config in LAYOUT_RESERVED_WORDS):
            widget_list.append({'type': w_config})
            continue

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
CLIENT_GRAPH_METRIC_ATTRS = ['name', 'title', 'color', 'warning_max_threshold',
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
            m_configs = w_configs[w_name].setdefault('metrics', [])
            for m_server_config in w_server_config['metrics']:
                attrs = dict((k, m_server_config[k])
                             for k in CLIENT_GRAPH_METRIC_ATTRS
                             if k in m_server_config)
                m_configs.append(attrs)

    #serialize client vars into a json string ready for javascript
    return 'var config = %s;' % (json.dumps(config),)


def build_widget_rows(configs):
    """
    Generates the widgets on each row. Each iteration,
    a row of widgets is yielded. Lvalue widgets are
    grouped together in a top to bottom fashion.
    """

    # a dict is used as a workaround, python 2 does not allow
    # assignment to the outer scope's variables
    ns = {
        # the current row
        'row': [],

        # rows already generated
        'rows': [],

        # the current row's column count
        'columns': 0,

        # queue of lvalue widgets for the current lvalue grouping
        'lvqueue': [],
    }

    def start_new_row():
        ns['rows'].append(ns['row'])
        ns['row'] = []
        ns['columns'] = 0

    def append_to_row(element, span):
        """
        Adds an element to the current row, or a new row if the element
        does not fit on the current row. A new row is then started
        if the current row is filled after the widget is added.
        """
        columns = ns['columns'] + span
        if (columns > MAX_COLUMN_SPAN):
            start_new_row()

        ns['row'].append(element)
        ns['columns'] = columns
        if (columns >= MAX_COLUMN_SPAN):
            start_new_row()

    def flush_lvalue_group():
        if len(ns['lvqueue']) == 0:
            return
        append_to_row(LValueGroup(ns['lvqueue']), 1)
        ns['lvqueue'] = []

    def add_lvalue(config):
        ns['lvqueue'].append(LValueWidget(config))
        if len(ns['lvqueue']) == LVALUE_GROUP_CAPACITY:
            flush_lvalue_group()

    def add_graph(config):
        # if the lvqueue is not empty, this needs to
        # be added to the row before the graph is added
        flush_lvalue_group()
        element = GraphWidget(config)
        append_to_row(element, config['width'])

    def add_newrow(config):
        """'fakes' the row being full"""
        # flush an lvalue group if the lvalue queue is not empty
        flush_lvalue_group()

    def add_newcol(config):
        """'Adds' a column"""
        # Graphs are added in a new column by default,
        # Flush any lvalue groups so new lvalues are
        # added in a new column
        flush_lvalue_group()

    fn_lookup = {
        'newcol': add_newcol,
        'newrow': add_newrow,
        'graph': add_graph,
        'lvalue': add_lvalue,
    }

    # iterate through the widget configs to create a list of rows
    for config in configs:
        add_widget = fn_lookup.get(config['type'], lambda x: x)
        add_widget(config)

    # flush an lvalue group if the lvalue queue is not empty
    flush_lvalue_group()

    # Append the last row (in the case that
    # it wasn't completely filled)
    if len(ns['row']) > 0:
        ns['rows'].append(ns['row'])

    return ns['rows']


class DashboardPage(Element):
    """
    An element for displaying an actual dashboard page.

    DashboardPage instances are created on page request.
    """

    loader = XMLString(resource_string(__name__,
                                       'templates/dashboard_page.xml'))

    def __init__(self, dashboard, is_shared):
        self.dashboard = dashboard
        self.is_shared = is_shared

    @renderer
    def brand_renderer(self, request, tag):
        href = '' if self.is_shared else '/'
        tag.fillSlots(brand_href_slot=href)
        return tag

    @renderer
    def dashboard_name_renderer(self, request, tag):
        return tag(self.dashboard.config['title'])

    @renderer
    def dashboard_container_renderer(self, request, tag):
        return self.dashboard


class Dashboard(Element):
    """
    Holds a dashboard's configuration data and widget elements.

    Dashboard instances are created when diamondash starts.
    """

    loader = XMLString(resource_string(__name__,
                                       'templates/dashboard_container.xml'))

    def __init__(self, config):
        self.config = parse_config(config)
        self.client_config = build_client_config(self.config)
        self.rows = build_widget_rows(self.config['widget_list'])

    @classmethod
    def dashboards_from_dir(cls, dir, defaults=None):
        """Gets a list of dashboard configs from a config dir"""
        dashboards = []

        for filename in listdir(dir):
            filepath = path.join(dir, filename)
            dashboard = Dashboard.from_config_file(filepath, defaults)
            dashboards.append(dashboard)

        return dashboards

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
        return self.config['widgets'].get(w_name, None)

    @renderer
    def widget_row_renderer(self, request, tag):
        for row in self.rows:
            yield WidgetRow(row)

    @renderer
    def config_script(self, request, tag):
        if self.client_config is not None:
            tag.fillSlots(client_config=self.client_config)
            return tag


class WidgetRow(Element):
    """Graph element that resides in a Dashboard element"""

    loader = XMLString(resource_string(__name__, 'templates/widget_row.xml'))

    def __init__(self, widgets):
        self.widgets = widgets

    @renderer
    def widget_renderer(self, request, tag):
        for widget in self.widgets:
            yield widget


class Widget(Element):
    """
    Abstract widget element that resides on a Dashboard.
    Subclasses need to assign an element to widget_element
    """

    loader = XMLString(resource_string(__name__, 'templates/widget.xml'))

    def __init__(self, config):
        self.config = config
        self.class_attrs = []
        self.widget_element = None

    @renderer
    def widget_renderer(self, request, tag):
        new_tag = tag.clone()

        self.class_attrs.extend(['widget', '%s-widget'
                                 % (self.config['type'],)])
        class_attr_str = ' '.join('%s' % attr
                                  for attr in self.class_attrs)

        new_tag.fillSlots(widget_title_slot=self.config['title'],
                          widget_class_slot=class_attr_str,
                          widget_id_slot=self.config['name'],
                          widget_element_slot=self.widget_element)
        return new_tag


class GraphWidget(Widget):
    """
    Graph subclass of Widget, providing a graph
    widget element from a template file
    """

    def __init__(self, config):
        Widget.__init__(self, config)
        widget_element_loader = XMLString(
            resource_string(__name__, 'templates/graph_widget.xml'))
        self.widget_element = Element(loader=widget_element_loader)

        span = {
            1: 'span4',
            2: 'span8',
            3: 'span12',
        }.get(config['width'], 1)
        self.class_attrs.append(span)


class LValueWidget(Widget):
    """
    LValue subclass of Widget, providing a graph
    widget element from a template file
    """

    def __init__(self, config):
        Widget.__init__(self, config)
        widget_element_loader = XMLString(
            resource_string(__name__, 'templates/lvalue_widget.xml'))
        self.widget_element = Element(loader=widget_element_loader)


class LValueGroup(Element):
    """A group of lvalue widgets displayed from top to bottom"""

    loader = XMLString(resource_string(__name__, 'templates/lvalue_group.xml'))

    def __init__(self, lvalue_widgets):
        self.lvalue_widgets = lvalue_widgets

    @renderer
    def lvalue_widget_renderer(self, request, tag):
        for lvalue_widget in self.lvalue_widgets:
            yield lvalue_widget


_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


def slugify(text):
    """Slugifies the passed in text"""
    result = []
    for word in _punct_re.split(text.lower()):
        result.extend(unidecode(word).split())
    return '-'.join(result)
