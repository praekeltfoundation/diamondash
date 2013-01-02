"""Web server for displaying dashboard components sourced from Graphite data"""

from os import path, listdir
from datetime import datetime
import json

import yaml
from twisted.web.client import getPage
from twisted.web.static import File
from twisted.web.template import Element, renderer, XMLString
from pkg_resources import resource_filename, resource_string
from klein import route, resource

from dashboard import DashboardPage, Dashboard, DASHBOARD_DEFAULTS


# We need resource imported for klein magic. This makes pyflakes happy.
resource = resource


CONFIG_FILENAME = 'diamondash.yml'
DEFAULT_PORT = '8080'
DEFAULT_CONFIG_DIR = 'etc/diamondash'
DEFAULT_GRAPHITE_URL = 'http://127.0.0.1:8000'
config = {}


def build_config(args=None):
    """
    Builds the config, initialised to defaults,
    updated with a config file and finally args
    """
    config = {
        'port': DEFAULT_PORT,
        'config_dir': DEFAULT_CONFIG_DIR,
        'graphite_url': DEFAULT_GRAPHITE_URL,
        'dashboards': {},
    }

    if args:
        config['config_dir'] = args.get('config_dir', DEFAULT_CONFIG_DIR)

    # load config file if it exists and update config
    if path.exists(config['config_dir']):
        filepath = '%s/%s' % (config['config_dir'], CONFIG_FILENAME)
        file_config = yaml.safe_load(open(filepath))
        config.update(file_config)

    # update config using args
    if args:
        config.update(args)

    dashboard_defaults = dict((k, config[k])
                              for k in DASHBOARD_DEFAULTS
                              if k in config)

    config = add_dashboards(config, dashboard_defaults)

    dashboard_ids = [{'name': d.config['name'],
                      'title': d.config['title']}
                     for d in config['dashboards'].values()]
    config['index'] = Index(dashboard_ids)

    return config


def add_dashboards(config, dashboard_defaults):
    """Adds the dashboards to the web server"""
    dashboards_path = '%s/dashboards' % (config['config_dir'],)

    if path.exists(dashboards_path):
        for filename in listdir(dashboards_path):
            filepath = '%s/%s' % (dashboards_path, filename)
            dashboard = Dashboard.from_config_file(filepath,
                                                   dashboard_defaults)
            dashboard_name = dashboard.config['name']
            config['dashboards'][dashboard_name] = dashboard

    return config


def format_results_for_graph(results, widget_config):
    """
    Formats the json output received from graphite into
    something usable by rickshaw
    """
    metrics = widget_config['metrics']

    # Find min length list to cut the lists at this length and keep d3 happy
    length = min([len(datapoints) for datapoints in results])

    formatted_data = {}
    for metric_name, datapoints in zip(metrics.keys(), results):
        metric_formatted_data = [{'x': x, 'y': y}
                                 for y, x in datapoints[:length]]
        formatted_data[metric_name] = metric_formatted_data
    return json.dumps(formatted_data)


_number_suffixes = ['', 'K', 'M', 'B', 'T']


EPS = 0.0001


def isint(n):
    """
    Checks if a number is equivalent to an integer value
    """
    if isinstance(n, (int, long)):
        return True

    return abs(n - int(n)) <= EPS


def format_value(n):
    mag = 0
    if abs(n) < 1000:
        return (str(int(n)) if isint(n)
                else '%.3f' % (n,))
    while abs(n) >= 1000 and mag < len(_number_suffixes) - 1:
        mag += 1
        n /= 1000.0
    return '%.3f%s' % (n, _number_suffixes[mag])


def format_time(time):
    # convert and cut of seconds
    time = str(datetime.utcfromtimestamp(time))[:-3]
    return time


def format_results_for_lvalue(data, widget_config):
    """
    Formats the json output received from graphite into
    something usable for lvalue widgets
    """
    time_range = widget_config['time_range']
    prev, lvalue, time = data
    from_time = format_time(time)
    to_time = format_time(time + time_range - 1)
    diff = lvalue - prev

    percentage = (diff / prev) * 100 if prev != 0 else 0
    percentage = "{0:.0f}%".format(percentage)

    lvalue = format_value(lvalue)
    diff = '%s%s' % ('+' if diff > 0 else '', format_value(diff),)

    formatted = json.dumps({
        'lvalue': lvalue,
        'from': from_time,
        'to': to_time,
        'diff': diff,
        'percentage': percentage,
    })

    return formatted


def zeroize_nulls(results):
    """
    Filters null y values in results obtained from graphite
    as zeroes (zeroize /is/ a word, wiktionary it)
    """
    return [[y, x] if y is not None else [0, x]
            for [y, x] in results if x is not None]


def skip_nulls(results):
    """Skips null y values in results obtained from graphite"""
    return [[y, x] for [y, x] in results
            if (y is not None) and (x is not None)]


def get_widget_null_filters(widget_config):
    """Returns the targets found in the passed in widget config"""
    # TODO optimise?
    metrics = widget_config['metrics']
    return [metric['null_filter'] for metric in metrics.values()]


def purify_results_for_graph(results, widget_config):
    """
    Fixes problems with the results obtained from
    graphite (eg. null values) for graph render
    requests
    """
    null_filter_strs = get_widget_null_filters(widget_config)

    # filter each metric according to is configured null filter
    purified = []
    for null_filter_str, datapoints in zip(null_filter_strs, results):
        null_filter = {
            'skip': skip_nulls,
            'zero': zeroize_nulls,
        }.get(null_filter_str, zeroize_nulls)
        purified.append(null_filter(datapoints))

    return purified


def aggregate_results_for_lvalue(data):
    """
    Takes in a list of datapoint lists and aggregates a tuple consisting
    of the following:
        - sum of previous y value
        - sum of last y value
        - maximum of last x value (latest time)
    """
    prev = sum((datapoints[-2][0] for datapoints in data
                if (len(datapoints) > 1 and datapoints[-2][0] is not None)))
    lvalue = sum((datapoints[-1][0] for datapoints in data
                if (len(datapoints) > 0 and datapoints[-1][0] is not None)))
    time = max((datapoints[-1][1] for datapoints in data
                if (len(datapoints) > 0 and datapoints[-1][1] is not None)))

    return prev, lvalue, time


def get_result_datapoints(data):
    """
    Obtains the datapoints from the result returned from
    graphite from a render request
    """
    return [metric['datapoints'] for metric in json.loads(data)]


def render_graph(data, widget_config):
    """
    Parses the passed in data into output useable for
    a graph widget
    """
    purified = purify_results_for_graph(data, widget_config)
    return format_results_for_graph(purified, widget_config)


def render_lvalue(data, widget_config):
    """
    Parses the passed in data into output useable for
    an lvalue widget
    """
    aggregated = aggregate_results_for_lvalue(data)
    return format_results_for_lvalue(aggregated, widget_config)


@route('/')
def show_index(request):
    return config['index']


@route('/static/')
def static(request):
    """Routing for all static files (css, js)"""
    return File(resource_filename(__name__, 'static'))


@route('/<string:dashboard_name>')
def show_dashboard(request, dashboard_name):
    dashboard_name = dashboard_name.encode('utf-8')
    return DashboardPage(config['dashboards'][dashboard_name], False)


@route('/render/<string:dashboard_name>/<string:widget_name>')
def render(request, dashboard_name, widget_name):
    """Routing for client render request"""
    # TODO check for invalid dashboards and widgets
    dashboard_name = dashboard_name.encode('utf-8')
    widget_name = widget_name.encode('utf-8')
    dashboard = config['dashboards'][dashboard_name]
    widget_config = dashboard.get_widget_config(widget_name)
    request_url = '%s/%s' % (config['graphite_url'],
                             widget_config['request_url'])

    d = getPage(request_url)
    d.addCallback(get_result_datapoints)

    render_widget = {
        'graph': render_graph,
        'lvalue': render_lvalue,
    }.get(widget_config['type'], render_graph)
    d.addCallback(render_widget, widget_config)

    return d


class Index(Element):
    """Index element with links to dashboards"""

    loader = XMLString(resource_string(__name__, 'templates/index.xml'))

    def __init__(self, dashboard_ids):
        self.dashboard_ids = dashboard_ids

    @renderer
    def dashboard_link_renderer(self, request, tag):
        for id in self.dashboard_ids:
            new_tag = tag.clone()

            href = '/%s' % (id['name'],)
            new_tag.fillSlots(dashboard_href_slot=href,
                              dashboard_title_slot=id['title'])
            yield new_tag
