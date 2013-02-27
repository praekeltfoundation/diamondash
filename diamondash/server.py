# -*- test-case-name: diamondash.tests.test_server -*-

"""Diamondash's web server functionality"""

import yaml
from glob import glob
from os import path

from twisted.web.static import File
from twisted.web.template import Element, renderer, XMLString, tags
from pkg_resources import resource_filename, resource_string
from klein import route, resource

from dashboard import Dashboard, DashboardPage

SHARED_URL_PREFIX = 'shared'

# We need resource imported for klein magic. This makes pyflakes happy.
resource = resource

# instance for the server
server = None


def configure(config_dir):
    global server
    server = DiamondashServer.from_config_dir(config_dir)


@route('/')
def show_index(request):
    return server.index


@route('/css/')
def serve_css(request):
    """Routing for all css files"""
    return server.resources.getChild('css', request)


@route('/js/')
def serve_js(request):
    """Routing for all js files"""
    return server.resources.getChild('js', request)


@route('/favicon.ico')
def favicon(request):
    return File(resource_filename(__name__, 'public/favicon.png'))


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
def handle_render_request(request, dashboard_name, widget_name):
    """Routing for client render request"""
    dashboard_name = dashboard_name.encode('utf-8')
    widget_name = widget_name.encode('utf-8')

    # get dashboard or return empty json object if it does not exist
    # TODO log non-existent dashboard requests
    dashboard = server.dashboards_by_name.get(dashboard_name, None)
    if dashboard is None:
        return "{}"

    # get widget or return empty json object if it does not exist
    # TODO log non-existent widget requests
    widget = dashboard.get_widget(widget_name)
    if widget is None:
        return "{}"

    return widget.handle_render_request(request)  # return a deferred


class DiamondashServer(object):
    """Contains the server's configuration options and dashboards"""

    ROOT_RESOURCE_DIR = resource_filename(__name__, '')
    CONFIG_FILENAME = 'diamondash.yml'

    def __init__(self, dashboards, resources):
        self.dashboards = []
        self.dashboards_by_name = {}
        self.dashboards_by_share_id = {}

        self.resources = resources
        self.index = Index()

        for dashboard in dashboards:
            self.add_dashboard(dashboard)

    @classmethod
    def dashboards_from_dir(cls, dashboards_dir, class_defaults={}):
        """Creates a list of dashboards from a config dir"""

        dashboards = []
        for filepath in glob(path.join(dashboards_dir, "*.yml")):
            dashboard = Dashboard.from_config_file(filepath, class_defaults)
            dashboards.append(dashboard)

        return dashboards

    @classmethod
    def create_resources(cls, pathname):
        return File(path.join(cls.ROOT_RESOURCE_DIR, pathname))

    @classmethod
    def from_config_dir(cls, config_dir):
        """Creates diamondash server from config file"""
        config_file = path.join(config_dir, cls.CONFIG_FILENAME)
        config = yaml.safe_load(open(config_file))

        class_defaults = config.get('defaults', {})
        dashboards_dir = path.join(config_dir, "dashboards")
        dashboards = cls.dashboards_from_dir(dashboards_dir, class_defaults)

        resources = cls.create_resources('public')
        return cls(dashboards, resources)

    def add_dashboard(self, dashboard):
        """Adds a dashboard to diamondash"""
        self.dashboards.append(dashboard)
        self.dashboards_by_name[dashboard.name] = dashboard

        share_id = dashboard.share_id
        if share_id is not None:
            self.dashboards_by_share_id[share_id] = dashboard

        self.index.add_dashboard(dashboard)


class Index(Element):
    """Index element with links to dashboards"""

    loader = XMLString(resource_string(__name__, 'views/index.xml'))

    def __init__(self, dashboards=[]):
        self.dashboard_list_items = []
        for dashboard in dashboards:
            self.add_dashboard(dashboard)

    def add_dashboard(self, dashboard):
        item = DashboardIndexListItem.from_dashboard(dashboard)
        self.dashboard_list_items.append(item)

    @renderer
    def dashboard_list_item_renderer(self, request, tag):
        for item in self.dashboard_list_items:
            yield item


class DashboardIndexListItem(Element):
    loader = XMLString(resource_string(
        __name__, 'views/index_dashboard_list_item.xml'))

    def __init__(self, title, url, shared_url_tag):
        self.title = title
        self.url = url
        self.shared_url_tag = shared_url_tag

    @classmethod
    def from_dashboard(cls, dashboard):
        url = '/%s' % (dashboard.name)

        share_id = dashboard.share_id
        if share_id is not None:
            shared_url = '/%s/%s' % (SHARED_URL_PREFIX, share_id)
            shared_url_tag = tags.a(shared_url, href=shared_url)
        else:
            shared_url_tag = ''

        return cls(dashboard.title, url, shared_url_tag)

    @renderer
    def dashboard_list_item_renderer(self, request, tag):
        tag.fillSlots(title_slot=self.title,
                      url_slot=self.url,
                      shared_url_slot=self.shared_url_tag)
        yield tag
