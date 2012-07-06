"""Web server for displaying dashboard components sourced from Graphite data"""

from os import path, listdir
import json
from urllib import urlencode

import yaml
from klein import resource, route
from twisted.web.client import getPage
from twisted.web.static import File
from twisted.web import server, static
from twisted.application import internet, service, strports
from pkg_resources import resource_filename

from dashboard import Dashboard


CONFIG_FILENAME = 'diamondash.yml'
DEFAULT_PORT = '8080'
DEFAULT_CONFIG_DIR = '/etc/diamondash'
DEFAULT_GRAPHITE_URL = 'http://127.0.0.1:8000'
DEFAULT_RENDER_PERIOD = 5
DEFAULT_REQUEST_INTERVAL = 2
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
            'render_period': DEFAULT_RENDER_PERIOD,
            'request_interval': DEFAULT_REQUEST_INTERVAL,
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

    config['client_config'] = {
            # convert to milliseconds and set client var
            'requestInterval': config['request_interval'] * 1000 
        }

    config = add_dashboards(config)

    return config


def add_dashboards(config):
    """Adds the dashboards to the web server"""
    dashboards_path = '%s/dashboards' % (config['config_dir'],)

    if path.exists(dashboards_path):
        for filename in listdir(dashboards_path):
            filepath = '%s/%s' % (dashboards_path, filename)
            dashboard = Dashboard.from_config_file(filepath,
                config['client_config'])
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


def construct_render_url(dashboard_name, widget_name):
    """
    Constructs the graphite render url based
    on the client's request uri
    """
    params = {
        'target': config['dashboards'][dashboard_name].get_widget_targets(widget_name),
        'from': '-%sminutes' % (config['render_period'],),
        'format': 'json'
        }
    render_url = "%s/render/?%s" % (config['graphite_url'], urlencode(params, True))
    return render_url


def format_render_results(results, dashboard_name, widget_name):
    """
    Formats the json output received from graphite into
    something usable by rickshaw
    """
    formatted_data = {}
    widget = config['dashboards'][dashboard_name].get_widget(widget_name)
    metrics = widget['metrics']

    # Find min length list to cut the lists at this length and keep d3 happy
    length = min([len(datapoints) for datapoints in results]);

    for metric_name, datapoints in zip(metrics.keys(), results):
        metric_formatted_data = [{'x': x, 'y': y} for y, x in datapoints[:length]]
        formatted_data[metric_name] = metric_formatted_data
    return json.dumps(formatted_data)


def zeroize_nulls(results):
    """
    Filters null y values in results obtained from graphite 
    as zeroes (zeroize /is/ a word, wiktionary it)
    """
    return [[y, x] if y is not None else [0, x]
            for [y, x] in results if x is not None]


def skip_nulls(results):
    """Skips null y values in results obtained from graphite"""
    return [[y, x] for [y, x] in results if (y is not None) and (x is not None)]


def purify_render_results(results, null_filter):
    """
    Fixes problems with the results obtained from
    graphite (eg. null values)
    """
    purified = [null_filter(datapoints) for datapoints in results]
    return purified


def get_render_result_datapoints(data):
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
    render_url = construct_render_url(dashboard_name, widget_name)

    d = getPage(render_url)
    d.addCallback(get_render_result_datapoints)
    null_filter = config['dashboards'][dashboard_name].get_widget(widget_name)['null_filter']
    d.addCallback(purify_render_results, skip_nulls if null_filter == 'skip' else zeroize_nulls)
    d.addCallback(format_render_results, dashboard_name, widget_name)
    return d
