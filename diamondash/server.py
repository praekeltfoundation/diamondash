# -*- test-case-name: diamondash.tests.test_server -*-

"""Diamondash's web server functionality"""

import yaml
import json
from os import path
from pkg_resources import resource_filename, resource_string

from twisted.web import http
from twisted.web.static import File
from twisted.web.template import Element, renderer, XMLString, tags
from twisted.internet.defer import maybeDeferred
from twisted.python import log
from klein import Klein

from diamondash import utils, ConfigError, PageElement
from dashboard import Dashboard, DashboardPage
from diamondash.widgets.dynamic import DynamicWidget


class DiamondashServer(object):
    """Contains the server's configuration options and dashboards"""

    app = Klein()

    ROOT_RESOURCE_DIR = resource_filename(__name__, '')
    CONFIG_FILENAME = 'diamondash.yml'

    def __init__(self, index, resources, dashboards, class_defaults={}):
        self.dashboards_by_name = {}
        self.dashboards_by_share_id = {}

        self.index = index
        self.resources = resources
        self.class_defaults = class_defaults

        for dashboard in dashboards:
            self.add_dashboard(dashboard)

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
        dashboards = Dashboard.dashboards_from_dir(dashboards_dir,
                                                   class_defaults)
        resources = cls.create_resources('public')
        return cls(Index(), resources, dashboards, class_defaults)

    def get_dashboard(self, name):
        return self.dashboards_by_name.get(name)

    def get_dashboard_by_share_id(self, share_id):
        return self.dashboards_by_share_id.get(share_id)

    def has_dashboard(self, name):
        return name in self.dashboards_by_name

    def add_dashboard(self, dashboard, overwrite=False):
        """Adds a dashboard to diamondash"""
        if not overwrite and self.has_dashboard(dashboard.name):
            return log.msg("Dashboard '%s' already exists" % dashboard.name)

        self.dashboards_by_name[dashboard.name] = dashboard

        share_id = dashboard.share_id
        if share_id is not None:
            self.dashboards_by_share_id[share_id] = dashboard

        self.index.add_dashboard(dashboard)

    def remove_dashboard(self, name):
        dashboard = self.get_dashboard(name)
        if dashboard is None:
            return None

        self.index.remove_dashboard(name)
        if dashboard.share_id is not None:
            del self.dashboards_by_share_id[dashboard.share_id]
        del self.dashboards_by_name[name]

    # Rendering
    # =========

    def render_error_response(self, request, code, description):
        request.setResponseCode(code)
        return ErrorPage(code, description)

    @app.route('/')
    def show_index(self, request):
        return self.index

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
        dashboard = self.get_dashboard(name.encode('utf-8'))
        if dashboard is None:
            return self.render_error_response(request, http.NOT_FOUND,
                "Dashboard '%s' does not exist" % name)
        return DashboardPage(dashboard)

    @app.route('/shared/<string:share_id>')
    def render_shared_dashboard(self, request, share_id):
        """Render a shared dashboard page"""
        dashboard = self.get_dashboard_by_share_id(share_id.encode('utf-8'))
        if dashboard is None:
            return self.render_error_response(request, http.NOT_FOUND,
                "Dashboard with share id '%s' does not exist or is not shared"
                % share_id)
        return DashboardPage(dashboard)

    # API
    # ===)

    @classmethod
    def api_response(cls, request, data, code=http.OK, headers={}):
        request.responseHeaders.setRawHeaders(
            'Content-Type', ['application/json'])
        for field, value in headers.iteritems():
            request.responseHeaders.setRawHeaders(field, value)

        request.setResponseCode(code)
        return json.dumps(data)

    @classmethod
    def api_error_response(cls, request, code, description):
        return cls.api_response(request, code=code,
                                data={'description': description})

    @classmethod
    def api_status_response(cls, request, name, status, code=http.OK):
        return cls.api_response(request, code=code, data={
            'name': name,
            'status': status,
        })

    @classmethod
    def api_get(cls, request, getter, *args, **kwargs):
        d = maybeDeferred(getter, *args, **kwargs)

        def trap_unhandled_error(f):
            f.trap(Exception)
            log.msg("Unhandled error occured during api request: %s" % f.value)
            return cls.api_error_response(request, http.INTERNAL_SERVER_ERROR,
                                          "Some unhandled error occurred")

        d.addCallback(lambda data: cls.api_response(request, data))
        d.addErrback(trap_unhandled_error)
        return d

    # Dashboard API
    # -------------

    @app.route('/api/dashboards/<string:name>', methods=['GET'])
    def api_get_dashboard_details(self, request, name):
        dashboard = self.get_dashboard(name.encode('utf-8'))
        if dashboard is None:
            return self.render_error_response(request, http.NOT_FOUND,
                "Dashboard '%s' does not exist" % name)
        return self.api_get(request, dashboard.get_details)

    @app.route('/api/dashboards', methods=['POST'])
    def api_create_dashboard(self, request):
        try:
            config = json.loads(request.content.read())
        except:
            return self.api_error_response(request, http.BAD_REQUEST,
               "Error parsing dashboard config as json object")

        if not isinstance(config, dict):
            return self.api_error_response(request, http.BAD_REQUEST,
               "Dashboard configs need to be json objects")

        if 'name' not in config:
            return self.api_error_response(request, http.BAD_REQUEST,
               "Dashboards need a name to be created")

        if self.has_dashboard(utils.slugify(config['name'])):
            return self.api_error_response(request, http.BAD_REQUEST,
               "Dashboard with name '%s' already exists")

        try:
            dashboard = Dashboard.from_config(config, self.class_defaults)
        except ConfigError:
            return self.api_error_response(request, http.BAD_REQUEST,
               "Error parsing dashboard config")

        self.add_dashboard(dashboard)
        return self.api_status_response(
            request, dashboard.name, 'CREATED', code=http.CREATED)

    @app.route('/api/dashboards/<string:name>', methods=['PUT'])
    def api_replace_dashboard(self, request, name):
        try:
            config = json.loads(request.content.read())
        except:
            return self.api_error_response(request, http.BAD_REQUEST,
               "Error parsing dashboard config as json object")

        if not isinstance(config, dict):
            return self.api_error_response(request, http.BAD_REQUEST,
               "Dashboard configs need to be json objects")

        config['name'] = name.encode('utf-8')

        try:
            dashboard = Dashboard.from_config(config, self.class_defaults)
        except ConfigError:
            return self.api_error_response(request, http.BAD_REQUEST,
               "Error parsing dashboard config")

        self.add_dashboard(dashboard, True)
        return self.api_response(request, {'name': dashboard.name})

    @app.route('/api/dashboards/<string:name>', methods=['DELETE'])
    def api_remove_dashboard(self, request, name):
        name = utils.slugify(name.encode('utf-8'))
        if not self.has_dashboard(name):
            return self.render_error_response(request, http.NOT_FOUND,
                "Dashboard '%s' does not exist" % name)

        self.remove_dashboard(name)
        return self.api_status_response(request, name, 'DELETED')

    # Widget API
    # -------------

    @app.route('/api/widgets/<string:dashboard_name>/<string:widget_name>',
               methods=['GET'])
    def api_get_widget_details(self, request, dashboard_name, widget_name):
        dashboard_name = dashboard_name.encode('utf-8')
        widget_name = widget_name.encode('utf-8')

        dashboard = self.get_dashboard(dashboard_name)
        if dashboard is None:
            return self.api_error_response(request, http.NOT_FOUND,
                "Dashboard '%s' does not exist" % dashboard_name)

        widget = dashboard.get_widget(widget_name)
        if widget is None:
            return self.api_error_response(request, http.NOT_FOUND,
                "Widget '%s' does not exist" % widget_name)

        return self.api_get(request, widget.get_details)

    @app.route(
        '/api/widgets/<string:dashboard_name>/<string:widget_name>/snapshot',
         methods=['GET'])
    def api_get_widget_snapshot(self, request, dashboard_name, widget_name):
        dashboard_name = dashboard_name.encode('utf-8')
        widget_name = widget_name.encode('utf-8')

        dashboard = self.get_dashboard(dashboard_name)
        if dashboard is None:
            return self.api_error_response(request, http.NOT_FOUND,
                "Dashboard '%s' does not exist" % dashboard_name)

        widget = dashboard.get_widget(widget_name)
        if widget is None:
            return self.api_error_response(request, http.NOT_FOUND,
                "Widget '%s' does not exist" % widget_name)

        if not isinstance(widget, DynamicWidget):
            return self.api_error_response(request, http.BAD_REQUEST,
                "Widget '%s' is not dynamic" % widget_name)

        return self.api_get(request, widget.get_snapshot)


class Index(PageElement):
    """Index element with links to dashboards"""

    loader = XMLString(resource_string(__name__, 'views/index.xml'))

    def __init__(self, dashboards=[]):
        self.dashboard_items = {}
        for dashboard in dashboards:
            self.add_dashboard(dashboard)

    def has_dashboard(self, name):
        return name in self.dashboard_items

    def add_dashboard(self, dashboard):
        item = DashboardIndexListItem.from_dashboard(dashboard)

        # we intentionally overwrite existing dashboard items with the same
        # dashboard name
        self.dashboard_items[dashboard.name] = item

    def remove_dashboard(self, name):
        if name not in self.dashboard_items:
            return None
        del self.dashboard_items[name]

    @renderer
    def dashboard_list_item_renderer(self, request, tag):
        for item in sorted(self.dashboard_items.values()):
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


class ErrorPage(PageElement):
    loader = XMLString(resource_string(
        __name__, 'views/error_page.xml'))

    def __init__(self, code, description):
        self.title = "(%s) %s" % (
            code, http.RESPONSES.get(code, "Error with Unknown Code"))
        self.description = description

    @renderer
    def header_renderer(self, request, tag):
        tag.fillSlots(title_slot=self.title, description_slot=self.description)
        yield tag
