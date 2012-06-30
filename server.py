"""Web server for displaying dashboard components sourced from Graphite data"""

import json
import yaml
from urllib import urlencode
from klein import resource, route
from twisted.web.client import getPage
from twisted.web.static import File
from dashboard import Dashboard


DEFAULT_CONFIG_FILEPATH = './etc/diamondash.yml' 
DEFAULT_GRAPHITE_URL = 'http://127.0.0.1:8000'
DEFAULT_RENDER_PERIOD = 5
DEFAULT_REQUEST_INTERVAL = 2


class ServerConfigFactory(object):
    """
    Holds configuration information for the
    diamondash web server
    """

    def __new__(cls, config):
        # TODO init from args
        # TODO load dashboards from directory of config files
        config = parse_config(config)
        config['dashboards'] = {}
        config['client_vars'] = 'var %s=%s;' % ('requestInterval',
                                                config['request_interval'])

    @classmethod 
    def parse_config(cls, config):
        if config['graphite_url'] not in config:
            config['graphite_url'] = DEFAULT_GRAPHITE_URL

        if config['render_period'] not in config:
            config['render_period'] = DEFAULT_RENDER_TIME_SPAN

        if config['request_interval'] not in config:
            config['request_interval'] = DEFAULT_REQUEST_INTERVAL

    @classmethod
    def from_config_file(cls, filepath):
        """Loads the diamondash configuration from a config file"""

        try: 
            config = yaml.safe_load(resource_string(__name__, filepath))
        except IOError:
            raise ConfigError('File %s not found.' % (filename,))

        return cls(config)


# initialise the server configuration
config = ServerConfigFactory(DEFAULT_CONFIG_FILEPATH)


def add_dashboard(dashboard):
    """Adds a new dashboard to the web server"""
    config.dashboards.update({dashboard.name: dashboard})


@route('/static/')
def static(request):
    """Routing for all static files (css, js)"""
    return File('./static')


@route('/')
def show_index(request):
    """Routing for homepage"""
    # TODO dashboard routing (instead of adding a new dashboard)
    # TODO handle multiple dashboards
    dashboard = Dashboard(config_filename='./etc/dashboard.yml')
    add_dashboard(dashboard)
    return dashboard


def construct_render_url(dashboard_name, widget_name):
    """
    Constructs the graphite render url based
    on the client's request uri
    """
    metric = config.dashboards[dashboard_name].widget_config[widget_name]['metric']
    params = {
        'target': metric,
        'from': '-%sminutes' % (config.config['render_period'],),
        'format': 'json'
        }
    render_url = "%s/render/?%s" % (config.config['graphite_url'], urlencode(params))
    return render_url


def format_render_results(results):
    """
    Formats the json output received from graphite into
    something usable by rickshaw
    """
    formatted_data = [{'x': x, 'y': y} for y, x in results]
    return json.dumps(formatted_data)


def purify_render_results(results):
    """
    Fixes problems with the results obtained from
    graphite (eg. null values)
    """
    # TODO decide what to do with y values based on config
    results = [[y, x] for [y, x] in results if (y is not None) and (x is not None)]
    return results


def get_datapoints(data):
    return json.loads(data)[0]['datapoints']


@route('/render/<string:dashboard_name>/<string:widget_name>')
def render(request, dashboard_name, widget_name):
    """Routing for client render request"""
    # TODO check for invalid dashboards
    render_url = construct_render_url(dashboard_name.encode('utf-8'), 
                                      widget_name.encode('utf-8'))
    d = getPage(render_url)
    d.addCallback(get_datapoints)
    d.addCallback(purify_render_results)
    d.addCallback(format_render_results)
    return d

class ConfigError(Exception):
    """Raised if the config file does not contain a compulsory attribute"""
