"""Web server for displaying dashboard components sourced from Graphite data"""

import json
from urllib import urlencode

import yaml
from klein import resource, route
from twisted.web.client import getPage
from twisted.web.static import File
from pkg_resources import resource_string, resource_stream, resource_filename

from dashboard import Dashboard

DEFAULT_GRAPHITE_URL = 'http://127.0.0.1:8000'
DEFAULT_RENDER_PERIOD = 5
DEFAULT_REQUEST_INTERVAL = 2

def build_config(overrides):
    config = {
            'graphite_url': DEFAULT_GRAPHITE_URL,
            'render_period': DEFAULT_RENDER_PERIOD,
            'request_interval': DEFAULT_REQUEST_INTERVAL,
            'dashboards': {},
        }

    config.update(overrides)

    config['client_vars'] = {
            'requestInterval': config['request_interval']
        }

    return config

def build_config_from_file(filename):
    """Loads the diamondash configuration from a config file"""

    try: 
        config = yaml.safe_load(open(filename))
    except IOError:
        raise ConfigError('File %s not found.' % (filename,))

    return build_config(config)

import os
# initialise the server configuration
config = build_config_from_file('%s/../etc/diamondash.yml' %
        (os.path.dirname(__file__),))

def add_dashboard(dashboard):
    """Adds a new dashboard to the web server"""
    dashboard_name = dashboard.config['name']
    config['dashboards'][dashboard_name] = dashboard


@route('/static/')
def static(request):
    """Routing for all static files (css, js)"""
    return File(resource_filename(__name__, 'static'))


@route('/')
def show_index(request):
    """Routing for homepage"""
    # TODO dashboard routing (instead of adding a new dashboard)
    # TODO handle multiple dashboards
    dashboard = Dashboard.from_config_file(
        '%s/../etc/diamondash.yml' %
        (os.path.dirname(__file__),))
    add_dashboard(dashboard)
    return dashboard


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


def format_render_results(results):
    """
    Formats the json output received from graphite into
    something usable by rickshaw
    """
    formatted_data = [{'x': x, 'y': y} for y, x in results]
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
    results = null_filter(results)
    # TODO other types of purification
    return results


def get_datapoints(data):
    return json.loads(data)[0]['datapoints']


@route('/render/<string:dashboard_name>/<string:widget_name>')
def render(request, dashboard_name, widget_name):
    """Routing for client render request"""
    # TODO check for invalid dashboards and widgets
    dashboard_name = dashboard_name.encode('utf-8')
    widget_name = widget_name.encode('utf-8')
    render_url = construct_render_url(dashboard_name, widget_name)

    d = getPage(render_url)
    d.addCallback(get_datapoints)
    null_filter = config['dashboards'][dashboard_name].get_widget(widget_name)['null_filter']
    d.addCallback(purify_render_results, skip_nulls if null_filter == 'skip' else zeroize_nulls)
    d.addCallback(format_render_results)
    return d
