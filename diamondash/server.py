"""Web server for displaying dashboard components sourced from Graphite data"""

from os import path, listdir
import json
from urllib import urlencode

import yaml
from twisted.web.client import getPage
from twisted.web.static import File
from pkg_resources import resource_filename
from klein import route, resource

from dashboard import Dashboard


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

    # TODO test

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

    config = add_dashboards(config)

    return config


def add_dashboards(config):
    """Adds the dashboards to the web server"""
    dashboards_path = '%s/dashboards' % (config['config_dir'],)

    if path.exists(dashboards_path):
        for filename in listdir(dashboards_path):
            filepath = '%s/%s' % (dashboards_path, filename)
            dashboard = Dashboard.from_config_file(filepath)
            dashboard_name = dashboard.config['name']
            config['dashboards'][dashboard_name] = dashboard

    return config


@route('/static/')
def static(request):
    """Routing for all static files (css, js)"""
    return File(resource_filename(__name__, 'static'))


@route('/')
def show_index(request):
    """Routing for homepage"""
    # TODO dashboard routing
    # TODO handle multiple dashboards
    # NOTE the not so nice looking line below is temporary
    return config['dashboards'].values()[0]


def get_widget_targets(widget_config):
    """Returns the targets found in the passed in widget config"""
    # TODO optimise?
    metrics = widget_config['metrics']
    return [metric['target'] for metric in metrics.values()]


def construct_render_url(widget_config):
    """
    Constructs the graphite render url based
    on the client's request uri
    """
    params = {
        'target': get_widget_targets(widget_config),
        'from': '-%ss' % (widget_config['render_period'],),
        'format': 'json'
    }
    render_url = "%s/render/?%s" % (config['graphite_url'],
                                    urlencode(params, True))
    return render_url


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


def format_results_for_lvalue(results, widget_config):
    """
    Formats the json output received from graphite into
    something usable for lvalue widgets
    """


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


def purify_results(results, widget_config):
    """
    Fixes problems with the results obtained from
    graphite (eg. null values)
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


def get_result_datapoints(data):
    """
    Obtaints the datapoints from the result returned from
    graphite from a render request
    """
    return [metric['datapoints'] for metric in json.loads(data)]


@route('/render/<string:dashboard_name>/<string:widget_name>')
def render(request, dashboard_name, widget_name):
    """Routing for client render request"""
    # TODO check for invalid dashboards and widgets
    dashboard_name = dashboard_name.encode('utf-8')
    widget_name = widget_name.encode('utf-8')
    dashboard = config['dashboards'][dashboard_name]
    widget_config = dashboard.get_widget_config(widget_name)

    # Construct the url
    render_url = construct_render_url(widget_config)

    d = getPage(render_url)
    d.addCallback(get_result_datapoints)
    d.addCallback(purify_results, widget_config)

    if widget_config['type'] == 'graph':
        format_results = format_results_for_graph
    elif widget_config['type'] == 'lvalue':
        format_results = format_results_for_lvalue
    d.addCallback(format_results, widget_config)

    return d
