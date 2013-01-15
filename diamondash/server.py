# -*- test-case-name: diamondash.tests.test_server -*-

"""Diamondash's web server functionality"""

import yaml
from os import path
from glob import glob

from twisted.web.static import File
from twisted.web.resource import Resource, NoResource
from twisted.web.template import Element, renderer, XMLString, tags
from pkg_resources import resource_filename, resource_string
from klein import route, resource

from utils import last_dir_in_path
from dashboard import Dashboard, DashboardPage

SHARED_URL_PREFIX = 'shared'

# We need resource imported for klein magic. This makes pyflakes happy.
resource = resource

# singleton instance for the server
server = None


def configure(dir):
    global server
    server = DiamondashServer.from_config_dir(dir)


@route('/')
def show_index(request):
    return server.index


@route('/public/')
def public(request):
    """Routing for all public files (css, js)"""
    return server.public_resources


@route('/public/js/widgets/<string:widget_type>/')
def widget_javascripts(request, widget_type):
    return server.get_widget_javascripts(widget_type)


@route('/public/css/widgets/<string:widget_type>/')
def widget_stylesheets(request, widget_type):
    return server.get_widget_stylesheets(widget_type)


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


def create_resource_from_path(pathname):
    res = Resource()
    filepaths = glob(pathname)
    for filepath in filepaths:
        res.putChild(path.basename(filepath), File(filepath))
    return res


class DiamondashServer(object):
    """Contains the server's configuration options and dashboards"""

    ROOT_RESOURCE_DIR = resource_filename(__name__, '')
    CONFIG_FILENAME = 'diamondash.yml'

    def __init__(self, dashboards, public_resources, widget_resources):
        self.dashboards = []
        self.dashboards_by_name = {}
        self.dashboards_by_share_id = {}

        self.public_resources = public_resources
        self.widget_resources = widget_resources

        self.index = Index()

        for dashboard in dashboards:
            self.add_dashboard(dashboard)

    @classmethod
    def create_widget_resources(cls):
        """
        Creates js and css resources, organised by widget type.
        """
        type_paths = glob(path.join(cls.ROOT_RESOURCE_DIR, 'widgets', '*/'))
        widget_javascripts = {}
        widget_stylesheets = {}

        for type_path in type_paths:
            # obtain widget type from the dir the widget module resides in
            type = last_dir_in_path(type_path)

            javascript_paths = path.join(type_path, '*.js')
            javascripts = create_resource_from_path(javascript_paths)
            widget_javascripts[type] = javascripts

            stylesheet_paths = path.join(type_path, '*.css')
            stylesheets = create_resource_from_path(stylesheet_paths)
            widget_stylesheets[type] = stylesheets

        return {
            'javascripts': widget_javascripts,
            'stylesheets': widget_stylesheets,
        }

    @classmethod
    def create_public_resources(cls):
        public_dir = path.join(cls.ROOT_RESOURCE_DIR, 'public')
        return File(public_dir)

    def get_widget_resource(self, resource_type, widget_type):
        # TODO log non-existent widget type requests
        try:
            res = self.widget_resources[resource_type][widget_type]
        except KeyError:
            return NoResource()
        else:
            return res

    def get_widget_javascripts(self, widget_type):
        return self.get_widget_resource('javascripts', widget_type)

    def get_widget_stylesheets(self, widget_type):
        return self.get_widget_resource('stylesheets', widget_type)

    @classmethod
    def from_config_dir(cls, config_dir):
        """Creates diamondash server from config file"""
        config_file = path.join(config_dir, cls.CONFIG_FILENAME)
        config = yaml.safe_load(open(config_file))

        dashboard_defaults = config.get('dashboard_defaults', {})
        widget_defaults = config.get('widget_defaults', {})
        dashboard_defaults['widget_defaults'] = widget_defaults

        dashboards_dir = path.join(config_dir, "dashboards")
        dashboards = Dashboard.dashboards_from_dir(dashboards_dir,
                                                   dashboard_defaults)
        public_resources = cls.create_public_resources()
        widget_resources = cls.create_widget_resources()

        return cls(dashboards, public_resources, widget_resources)

    def add_dashboard(self, dashboard):
        """Adds a dashboard to diamondash"""
        self.dashboards.append(dashboard)

        name = dashboard.name
        self.dashboards_by_name[name] = dashboard

        share_id = dashboard.share_id
        if share_id is not None:
            self.dashboards_by_share_id[share_id] = dashboard

        self.index.add_dashboard(dashboard)


class Index(Element):
    """Index element with links to dashboards"""

    loader = XMLString(resource_string(__name__, 'templates/index.xml'))

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
        __name__, 'templates/index_dashboard_list_item.xml'))

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
