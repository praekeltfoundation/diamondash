# -*- test-case-name: diamondash.tests.test_dashboard -*-

"""Dashboard functionality for the diamondash web app"""

import json
from pkg_resources import resource_string

from twisted.web.template import Element, renderer, XMLString

from diamondash import utils, PageElement
from diamondash.config import Config, ConfigError
from diamondash.widgets.dynamic import DynamicWidget


class DashboardConfig(Config):
    DEFAULTS = {
        'request_interval': '60s'
    }

    @classmethod
    def parse(cls, config):
        if 'name' not in config:
            raise ConfigError('Dashboard name not specified.')

        name = config['name']
        config.setdefault('title', name)
        name = utils.slugify(name)
        config['name'] = name

        if 'widgets' not in config:
            raise ConfigError("Dashboard '%s' has no widgets" % name)

        backend_config = config.pop('backend', {})
        config['widgets'] = [
            cls.parse_widget(w, backend_config) for w in config['widgets']]

        # request interval is converted to milliseconds for client side
        request_interval = utils.parse_interval(config.pop('request_interval'))
        request_interval = utils.to_client_interval(request_interval)

        config['client_config'] = {
            'name': name,
            'requestInterval': request_interval,
            'widgets': [
                w['client_config'] for w in config['widgets']
                if not Dashboard.is_layout_fn(w)]
        }

        return config

    @classmethod
    def parse_widget(cls, config, backend_config):
        if Dashboard.is_layout_fn(config):
            return config

        type_cls = utils.load_class_by_string(config['type'])

        if issubclass(type_cls, DynamicWidget):
            config['backend'] = utils.add_dicts(
                backend_config,
                config.get('backend', {}))

        config_cls = cls.for_type(config['type'])
        return config_cls.from_dict(config)


class Dashboard(Element):
    """
    Holds a dashboard's configuration data and widget elements.

    Dashboard instances are created when diamondash starts.
    """

    CONFIG_CLS = DashboardConfig

    # the max number of columns allowed by Bootstrap's grid system
    MAX_WIDTH = 12

    LAYOUT_FUNCTIONS = {'newrow': '_new_row'}

    loader = XMLString(
        resource_string(__name__, 'views/dashboard_container.xml'))

    def __init__(self, config):
        self.config = config

        self.widgets = []
        self.widgets_by_name = {}
        self.last_row = WidgetRow()
        self.rows = [self.last_row]

        for widget in self.config['widgets']:
            self.add_widget(widget)

    @classmethod
    def is_layout_fn(cls, obj):
        return isinstance(obj, str) and obj in cls.LAYOUT_FUNCTIONS

    def apply_layout_fn(self, name):
        return getattr(self, self.LAYOUT_FUNCTIONS[name])()

    def _new_row(self):
        self.last_row = WidgetRow()
        self.rows.append(self.last_row)

    def add_widget(self, config):
        """Adds a widget to the dashboard. """

        if self.is_layout_fn(config):
            self.apply_layout_fn(config)
        else:
            if self.last_row.width + config['width'] > self.MAX_WIDTH:
                self._new_row()

            type_cls = utils.load_class_by_string(config['type'])
            widget = type_cls(config)

            self.widgets_by_name[config['name']] = widget
            self.widgets.append(widget)

            # append to the last row
            self.last_row.add_widget(WidgetContainer(widget))

    def get_widget(self, name):
        """Returns a widget using the passed in widget name."""
        return self.widgets_by_name.get(name, None)

    def get_details(self):
        """Returns data describing the dashboard."""
        return self.config

    @renderer
    def dashboard_title_renderer(self, request, tag):
        return tag(self.config['title'])

    @renderer
    def widget_row_renderer(self, request, tag):
        for row in self.rows:
            yield row

    @renderer
    def init_script_renderer(self, request, tag):
        client_config = json.dumps(self.config['client_config'])
        tag.fillSlots(client_config_slot=client_config)
        return tag


class WidgetRow(Element):
    """
    A row of Widget elements on a dashboard

    WidgetRow instances are created when diamondash starts.
    """

    loader = XMLString(resource_string(__name__, 'views/widget_row.xml'))

    def __init__(self):
        self.width = 0
        self.widgets = []

    def add_widget(self, widget):
        self.widgets.append(widget)
        self.width += widget.width

    @renderer
    def widget_renderer(self, request, tag):
        for widget in self.widgets:
            contained_widget = widget
            yield contained_widget


class WidgetContainer(Element):
    """
    Widget container element holding a widget element.

    WidgetContainer instances are created when diamondash starts.
    """

    loader = XMLString(resource_string(__name__, 'views/widget_container.xml'))

    def __init__(self, widget):
        self.widget = widget
        self.width = widget.config['width']
        span_class = "col-md-%s" % widget.config['width']
        self.classes = " ".join([
            'widget', widget.config.TYPE_NAME, span_class])

    @renderer
    def widget_renderer(self, request, tag):
        widget = self.widget
        tag.fillSlots(
            id_slot=widget.config['name'],
            title_slot=widget.config['title'],
            class_slot=self.classes,
            widget_slot=widget)

        return tag


class DashboardPage(PageElement):
    """
    An element for displaying an actual dashboard page.

    DashboardPage instances are created on page request.
    """

    loader = XMLString(resource_string(__name__, 'views/dashboard_page.xml'))

    def __init__(self, dashboard, shared=False):
        self.dashboard = dashboard
        self.shared = shared

    @renderer
    def brand_renderer(self, request, tag):
        href = '' if not self.shared else '/'
        tag.fillSlots(brand_href_slot=href)
        return tag

    @renderer
    def dashboard_container_renderer(self, request, tag):
        return self.dashboard
