# -*- test-case-name: diamondash.tests.test_server -*-

"""Diamondash's web server functionality"""

import yaml
import json
from os import path
from glob import glob
from pkg_resources import resource_filename, resource_string

from twisted.web import http
from twisted.web.static import File
from twisted.web.template import Element, renderer, XMLString, tags
from twisted.internet.defer import maybeDeferred
from twisted.python import log
from klein import Klein

from diamondash import utils, PageElement
from diamondash.config import Config, ConfigError
from dashboard import DashboardConfig, Dashboard, DashboardPage
from diamondash.widgets.dynamic import DynamicWidget


class DiamondashConfig(Config):
    FILENAME = 'diamondash.yml'

    DEFAULTS = {
        'poll_interval': '60s',
        'backend': {
            'type': 'diamondash.backends.graphite.GraphiteBackend',
            'url': 'http://127.0.0.1:8080',
        }
    }

    @classmethod
    def parse(cls, config):
        dashboard_configs = sorted(
            config.get('dashboards', []),
            key=lambda d: d['name'])

        config['dashboards'] = [
            DashboardConfig(cls._set_dashboard_defaults(config, d))
            for d in dashboard_configs]

        return config

    @classmethod
    def from_dir(cls, dirname):
        config = yaml.safe_load(open(path.join(dirname, cls.FILENAME)))

        config['dashboards'] = [
            yaml.safe_load(open(filename))
            for filename in glob(path.join(dirname, 'dashboards', '*.yml'))]

        return cls(config)

    @classmethod
    def _set_dashboard_defaults(self, config, dashboard_config):
        return utils.add_dicts({
            'backend': config['backend'],
            'poll_interval': config['poll_interval'],
        }, dashboard_config)

    def set_dashboard_defaults(self, dashboard_config):
        return self._set_dashboard_defaults(self, dashboard_config)


class DiamondashServer(object):
    """Contains the server's configuration options and dashboards"""

    app = Klein()
    CONFIG_CLS = DiamondashConfig
    RESOURCE_DIRNAME = path.join(resource_filename(__name__, ''), 'public')

    def __init__(self, config):
        self.config = config

        self.dashboards_by_name = {}
        self.dashboards_by_share_id = {}

        self.index = Index()
        self.resources = self.create_resources()

        for dashboard_config in config['dashboards']:
            self.add_dashboard(dashboard_config)

    @classmethod
    def create_resources(cls):
        return File(path.join(cls.RESOURCE_DIRNAME))

    def get_dashboard(self, name):
        return self.dashboards_by_name.get(name)

    def get_dashboard_by_share_id(self, share_id):
        return self.dashboards_by_share_id.get(share_id)

    def has_dashboard(self, name):
        return name in self.dashboards_by_name

    def add_dashboard(self, config, overwrite=False):
        """Adds a dashboard to diamondash"""
        if not overwrite and self.has_dashboard(config['name']):
            return log.msg("Dashboard '%s' already exists" % config['name'])

        dashboard = Dashboard(config)
        self.dashboards_by_name[config['name']] = dashboard

        if 'share_id' in config:
            self.dashboards_by_share_id[config['share_id']] = dashboard

        self.index.add_dashboard(dashboard)

    def remove_dashboard(self, name):
        dashboard = self.get_dashboard(name)
        if dashboard is None:
            return None

        self.index.remove_dashboard(name)
        if 'share_id' in dashboard.config:
            del self.dashboards_by_share_id[dashboard.config['share_id']]
        del self.dashboards_by_name[name]

    # Rendering
    # =========

    def render_error_response(self, request, message, code):
        request.setResponseCode(code)
        return ErrorPage(code, message)

    @app.route('/')
    def show_index(self, request):
        return self.index

    @app.route('/public/<string:res_type>/<string:name>')
    def serve_resource(self, request, res_type, name):
        """Routing for all public resources"""
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
            return self.render_error_response(
                request,
                code=http.NOT_FOUND,
                message="Dashboard '%s' does not exist" % name)
        return DashboardPage(dashboard)

    @app.route('/shared/<string:share_id>')
    def render_shared_dashboard(self, request, share_id):
        """Render a shared dashboard page"""
        dashboard = self.get_dashboard_by_share_id(share_id.encode('utf-8'))
        if dashboard is None:
            return self.render_error_response(
                request,
                code=http.NOT_FOUND,
                message=(
                    "Dashboard with share id '%s' does not exist "
                    "or is not shared" % share_id))
        return DashboardPage(dashboard, shared=True)

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
    def api_success_response(cls, request, data=None, code=http.OK):
        return cls.api_response(request, code=code, data={
            'success': True,
            'data': data,
        })

    @classmethod
    def api_error_response(cls, request, message, code):
        return cls.api_response(request, code=code, data={
            'success': False,
            'message': message,
        })

    @classmethod
    def api_get(cls, request, getter, *args, **kwargs):
        d = maybeDeferred(getter, *args, **kwargs)

        def trap_unhandled_error(f):
            f.trap(Exception)
            log.msg("Unhandled error occured during api request: %s" % f.value)
            return cls.api_error_response(
                request,
                code=http.INTERNAL_SERVER_ERROR,
                message="Some unhandled error occurred")

        d.addCallback(lambda data: cls.api_response(request, data))
        d.addErrback(trap_unhandled_error)
        return d

    # Dashboard API
    # -------------

    @app.route('/api/dashboards/<string:name>', methods=['GET'])
    def api_get_dashboard_details(self, request, name):
        dashboard = self.get_dashboard(name.encode('utf-8'))
        if dashboard is None:
            return self.render_error_response(
                request,
                code=http.NOT_FOUND,
                message="Dashboard '%s' does not exist" % name)
        return self.api_get(request, dashboard.get_details)

    @app.route('/api/dashboards', methods=['POST'])
    def api_create_dashboard(self, request):
        try:
            config = json.loads(request.content.read())
        except:
            return self.api_error_response(
                request,
                code=http.BAD_REQUEST,
                message="Error parsing dashboard config as json object")

        if not isinstance(config, dict):
            return self.api_error_response(
                request,
                code=http.BAD_REQUEST,
                message="Dashboard configs need to be json objects")

        if 'name' not in config:
            return self.api_error_response(
                request,
                code=http.BAD_REQUEST,
                message="Dashboards need a name to be created")

        if self.has_dashboard(utils.slugify(config['name'])):
            return self.api_error_response(
                request,
                code=http.BAD_REQUEST,
                message="Dashboard with name '%s' already exists")

        try:
            config = DashboardConfig(config)
        except ConfigError, e:
            return self.api_error_response(
                request,
                code=http.BAD_REQUEST,
                message="Error parsing dashboard config: %r" % e)

        self.add_dashboard(config)
        return self.api_success_response(
            request,
            data=self.get_dashboard(config['name']).get_details(),
            code=http.CREATED)

    @app.route('/api/dashboards', methods=['PUT'])
    def api_replace_dashboard(self, request):
        try:
            config = json.loads(request.content.read())
        except:
            return self.api_error_response(
                request,
                code=http.BAD_REQUEST,
                message="Error parsing dashboard config as json object")

        if not isinstance(config, dict):
            return self.api_error_response(
                request,
                code=http.BAD_REQUEST,
                message="Dashboard configs need to be json objects")

        try:
            config = DashboardConfig(config)
        except ConfigError, e:
            return self.api_error_response(
                request,
                code=http.BAD_REQUEST,
                message="Error parsing dashboard config: %r" % e)

        self.add_dashboard(config, True)
        return self.api_success_response(
            request,
            data=self.get_dashboard(config['name']).get_details())

    @app.route('/api/dashboards/<string:name>', methods=['DELETE'])
    def api_remove_dashboard(self, request, name):
        name = utils.slugify(name.encode('utf-8'))
        if not self.has_dashboard(name):
            return self.render_error_response(
                request,
                code=http.NOT_FOUND,
                message="Dashboard '%s' does not exist" % name)

        self.remove_dashboard(name)
        return self.api_success_response(request)

    # Widget API
    # -------------

    @app.route('/api/widgets/<string:dashboard_name>/<string:widget_name>',
               methods=['GET'])
    def api_get_widget_details(self, request, dashboard_name, widget_name):
        dashboard_name = dashboard_name.encode('utf-8')
        widget_name = widget_name.encode('utf-8')

        dashboard = self.get_dashboard(dashboard_name)
        if dashboard is None:
            return self.api_error_response(
                request,
                code=http.NOT_FOUND,
                message="Dashboard '%s' does not exist" % dashboard_name)

        widget = dashboard.get_widget(widget_name)
        if widget is None:
            return self.api_error_response(
                request,
                code=http.NOT_FOUND,
                message="Widget '%s' does not exist" % widget_name)

        return self.api_get(request, widget.get_details)

    @app.route(
        '/api/widgets/<string:dashboard_name>/<string:widget_name>/snapshot',
        methods=['GET'])
    def api_get_widget_snapshot(self, request, dashboard_name, widget_name):
        dashboard_name = dashboard_name.encode('utf-8')
        widget_name = widget_name.encode('utf-8')

        dashboard = self.get_dashboard(dashboard_name)
        if dashboard is None:
            return self.api_error_response(
                request,
                code=http.NOT_FOUND,
                message="Dashboard '%s' does not exist" % dashboard_name)

        widget = dashboard.get_widget(widget_name)
        if widget is None:
            return self.api_error_response(
                request,
                code=http.NOT_FOUND,
                message="Widget '%s' does not exist" % widget_name)

        if not isinstance(widget, DynamicWidget):
            return self.api_error_response(
                request,
                code=http.BAD_REQUEST,
                message="Widget '%s' is not dynamic" % widget_name)

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
        self.dashboard_items[dashboard.config['name']] = item

    def remove_dashboard(self, name):
        if name not in self.dashboard_items:
            return None
        del self.dashboard_items[name]

    @renderer
    def dashboard_list_item_renderer(self, request, tag):
        for name, item in sorted(self.dashboard_items.iteritems()):
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
        url = '/%s' % (dashboard.config['name'])

        if 'share_id' in dashboard.config:
            shared_url = '/shared/%s' % dashboard.config['share_id']
            shared_url_tag = tags.a(shared_url, href=shared_url)
        else:
            shared_url_tag = ''

        return cls(dashboard.config['title'], url, shared_url_tag)

    @renderer
    def dashboard_list_item_renderer(self, request, tag):
        tag.fillSlots(title_slot=self.title,
                      url_slot=self.url,
                      shared_url_slot=self.shared_url_tag)
        yield tag


class ErrorPage(PageElement):
    loader = XMLString(resource_string(
        __name__, 'views/error_page.xml'))

    def __init__(self, code, message):
        self.title = "(%s) %s" % (
            code, http.RESPONSES.get(code, "Error with Unknown Code"))
        self.message = message

    @renderer
    def header_renderer(self, request, tag):
        tag.fillSlots(title_slot=self.title, message_slot=self.message)
        yield tag
