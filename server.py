"""Web server for displaying dashboard components sourced from Graphite data"""

import json
from urllib import urlencode
from klein import resource, route
from twisted.web.client import getPage
from twisted.web.static import File
from dashboard import Dashboard

DEFAULT_GRAPHITE_URL = "http://127.0.0.1:8000"
DEFAULT_RENDER_TIME_SPAN = 5

class ServerConfig(object):
    """
    Holds configuration information for the
    diamondash web server
    """

    def __init__(self, graphite_url=None, render_time_span=None):
        # TODO init from args or config file
        # TODO allow mulitiple dashboards

        if graphite_url is None:
            graphite_url = DEFAULT_GRAPHITE_URL

        if render_time_span is None:
            render_time_span = DEFAULT_RENDER_TIME_SPAN

        self.graphite_url = graphite_url
        self.render_time_span = render_time_span
        self.dashboards = {}


# initialise the server configuration
config = ServerConfig()


def add_dashboard(dashboard):
    """Adds a new dashboard to the web server"""
    config.dashboards.update({dashboard.name: dashboard})


@route('/static/')
def static(request):
    """Routing for all static files (css, js)"""
    return File("./static")


@route('/')
def show_index(request):
    """Routing for homepage"""
    # TODO dashboard routing (instead of adding a new dashboard)
    # TODO handle multiple dashboards
    dashboard = Dashboard.from_config_file('./etc/test_dashboard.yml')
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
        'from': '-%sminutes' % (config.render_time_span,),
        'format': 'json'
        }
    render_url = "%s/render/?%s" % (config.graphite_url, urlencode(params))
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
    results = [[y, x] for [y, x] in results if (y is not None) or (x is not None)]
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
