"""Web server for displaying dashboard components sourced from Graphite data"""

import json
from os import path
from datetime import datetime

import yaml
from twisted.web.client import getPage
from twisted.web.static import File
from twisted.web.template import Element, renderer, XMLString, tags
from twisted.python import log
from pkg_resources import resource_filename, resource_string
from klein import route, resource

from dashboard import Dashboard, DashboardPage


# We need resource imported for klein magic. This makes pyflakes happy.
resource = resource

SHARED_URL_PREFIX = 'shared'
CONFIG_FILENAME = 'diamondash.yml'

DEFAULT_GRAPHITE_URL = 'http://127.0.0.1:8000'

DASHBOARD_DEFAULTS = {
    'request_interval': 2,
    'default_widget_type': 'graph',
}


class DiamondashServer(object):
    """Contains the server's configuration options and dashboards"""

    def __init__(self, graphite_url, dashboards):
        self.graphite_url = graphite_url

        self.dashboards = []
        self.dashboards_by_name = {}
        self.dashboards_by_share_id = {}

        for dashboard in dashboards:
            self.add_dashboard(dashboard)

        self.index = Index(self.dashboards)

    @classmethod
    def from_config_dir(cls, config_dir):
        """Creates diamondash server from config file"""
        # TODO test

        config_file = path.join(config_dir, CONFIG_FILENAME,)
        config = yaml.safe_load(open(config_file))

        graphite_url = config.get('graphite_url', DEFAULT_GRAPHITE_URL)

        dashboard_defaults = {}
        for key, default_value in DASHBOARD_DEFAULTS.iteritems():
            dashboard_defaults[key] = config.get(key, default_value)

        dashboards_dir = path.join(config_dir, "dashboards")
        dashboards = Dashboard.dashboards_from_dir(dashboards_dir,
                                                   dashboard_defaults)
        return cls(graphite_url, dashboards)

    def add_dashboard(self, dashboard):
        """Adds a dashboard to diamondash"""
        self.dashboards.append(dashboard)

        name = dashboard.config['name']
        self.dashboards_by_name[name] = dashboard

        share_id = dashboard.config.get('share_id', None)
        if share_id is not None:
            self.dashboards_by_share_id[share_id] = dashboard


# singleton instance for the server
server = None


def configure(dir):
    global server
    server = DiamondashServer.from_config_dir(dir)


def format_results_for_graph(results, widget_config):
    """
    Formats the json output received from graphite into
    something usable by rickshaw
    """
    metrics = widget_config['metrics']

    # Find min length list to cut the lists at this length and keep d3 happy
    length = min([len(datapoints) for datapoints in results])

    formatted_data = {}
    for metric, datapoints in zip(metrics, results):
        m_name = metric['name']
        m_formatted_data = [{'x': x, 'y': y} for y, x in datapoints[:length]]
        formatted_data[m_name] = m_formatted_data
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
    return [metric['null_filter'] for metric in metrics]


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

    # set time to 0 if all metric results are empty
    times = [datapoints[-1][1] for datapoints in data
             if (len(datapoints) > 0 and datapoints[-1][1] is not None)]
    time = 0 if not times else max(times)

    return prev, lvalue, time


def get_result_datapoints(data, widget_config):
    """
    Obtains the datapoints from the result returned from
    graphite from a render request
    """
    data = json.loads(data)
    datapoints_by_target = dict((m['target'], m['datapoints']) for m in data)
    return [datapoints_by_target.get(t, [])
            for t in widget_config['target_keys']]


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
    return server.index


@route('/static/')
def static(request):
    """Routing for all static files (css, js)"""
    return File(resource_filename(__name__, 'static'))


@route('/<string:name>')
def show_dashboard(request, name):
    """Show a non-shared dashboard page"""
    # TODO handle invalid name references
    name = name.encode('utf-8')
    return DashboardPage(server.dashboards_by_name[name], False)


@route('/%s/<string:share_id>' % SHARED_URL_PREFIX)
def show_shared_dashboard(request, share_id):
    """Show a shared dashboard page"""
    # TODO handle invalid share id references
    share_id = share_id.encode('utf-8')
    return DashboardPage(server.dashboards_by_share_id[share_id], True)


@route('/render/<string:dashboard_name>/<string:widget_name>')
def render(request, dashboard_name, widget_name):
    """Routing for client render request"""
    dashboard_name = dashboard_name.encode('utf-8')
    widget_name = widget_name.encode('utf-8')

    # get dashboard or return empty json object if it does not exist
    dashboard = server.dashboards_by_name.get(dashboard_name, None)
    if dashboard is None:
        return "{}"

    # get widget config or return empty json object if it does not exist
    widget_config = dashboard.get_widget_config(widget_name)
    if widget_config is None:
        return "{}"

    request_url = '/'.join(s.strip('/') for s in (
        server.graphite_url, widget_config['request_url']))
    d = getPage(request_url)

    d.addCallback(get_result_datapoints, widget_config)

    render_widget = {
        'graph': render_graph,
        'lvalue': render_lvalue,
    }.get(widget_config['type'], render_graph)
    d.addCallback(render_widget, widget_config)

    return d


class Index(Element):
    """Index element with links to dashboards"""

    loader = XMLString(resource_string(__name__, 'templates/index.xml'))

    def __init__(self, dashboards):
        self.dashboards = dashboards

    @renderer
    def dashboard_link_renderer(self, request, tag):
        for dashboard in self.dashboards:
            dashboard_config = dashboard.config
            new_tag = tag.clone()

            href = '/%s' % (dashboard_config['name'],)

            share_id = dashboard_config.get('share_id', None)
            if share_id is not None:
                shared_url = '/%s/%s' % (SHARED_URL_PREFIX, share_id)
                shared_url_tag = tags.a(shared_url, href=shared_url)
            else:
                shared_url_tag = ''

            new_tag.fillSlots(dashboard_href_slot=href,
                              dashboard_title_slot=dashboard_config['title'],
                              dashboard_shared_url_slot=shared_url_tag)
            yield new_tag
