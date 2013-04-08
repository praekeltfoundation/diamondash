# -*- test-case-name: diamondash.tests.test_server -*-

"""Diamondash's web server functionality"""

import yaml
import json
from glob import glob
from os import path
from pkg_resources import resource_filename, resource_string

from twisted.web.static import File
from twisted.web.template import Element, renderer, XMLString, tags
from twisted.internet.defer import maybeDeferred
from twisted.python import log
from klein import Klein

from diamondash import utils
from dashboard import Dashboard, DashboardPage


class DiamondashServer(object):
    """Contains the server's configuration options and dashboards"""

    app = Klein()

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

    def has_dashboard(self, name):
        return utils.slugify(name) in self.dashboards_by_name

    def add_dashboard(self, dashboard):
        """Adds a dashboard to diamondash"""
        self.dashboards.append(dashboard)
        self.dashboards_by_name[dashboard.name] = dashboard

        share_id = dashboard.share_id
        if share_id is not None:
            self.dashboards_by_share_id[share_id] = dashboard

        self.index.add_dashboard(dashboard)

    # Rendering
    # =========

    @app.route('/')
    def show_index(self, request):
        return self.index

    @app.route('/css/')
    def serve_css(self, request):
        """Routing for all css files"""
        return self.resources.getChild('css', request)

    @app.route('/js/')
    def serve_js(self, request):
        """Routing for all js files"""
        return self.resources.getChild('js', request)

    @app.route('/<any(css, js):res_type>/<string:name>')
    @app.route('/shared/<any(css, js):res_type>/<string:name>')
    def serve_static_resource(self, request, res_type, name):
        """Routing for all css files"""
        res_dir = self.resources.getChild(res_type, request)
        return res_dir.getChild(name, request)

    @app.route('/favicon.ico')
    def favicon(self, request):
        return File(resource_filename(__name__, 'public/favicon.png'))

    @app.route('/<string:name>')
    def render_dashboard(self, request, name):
        """Render a non-shared dashboard page"""
        # TODO handle invalid name references
        name = name.encode('utf-8')
        return DashboardPage(self.dashboards_by_name[name], False)

    @app.route('/shared/<string:share_id>')
    def render_shared_dashboard(self, request, share_id):
        """Render a shared dashboard page"""
        # TODO handle invalid share id references
        share_id = share_id.encode('utf-8')
        return DashboardPage(self.dashboards_by_share_id[share_id], True)

    # API
    # ===

    # Dashboard API
    # -------------

    @app.route('/api/dashboards', methods=['POST'])
    def create_dashboard(self, request):
        raw_config = json.loads(request.content.read())

        if 'name' not in raw_config:
            # TODO
            return

        if self.has_dashboard(raw_config['name']):
            # TODO
            pass

    # Widget API
    # -------------

    @app.route('/api/widgets/<string:dashboard_name>/<string:widget_name>',
               methods=['GET'])
    def get_widget_data(self, request, dashboard_name, widget_name):
        #request.setHeader('Content-Type', 'application/json')

        dashboard_name = dashboard_name.encode('utf-8')
        widget_name = widget_name.encode('utf-8')

        # get dashboard or return empty json object if it does not exist
        dashboard = self.dashboards_by_name.get(dashboard_name)
        if dashboard is None:
            # TODO err resp code
            log.msg("Bad widget API request: Dashboard '%s' does not exist." %
                    dashboard_name)
            return "{}"

        # get widget or return empty json object if it does not exist
        widget = dashboard.get_widget(widget_name)
        if widget is None:
            # TODO err resp code
            log.msg("Bad widget API request: Widget '%s' does not exist." %
                    widget_name)
            return "{}"

        d = maybeDeferred(widget.get_data)
        d.addCallback(json.dumps)
        return d


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
            shared_url = '/shared/%s' % share_id
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
