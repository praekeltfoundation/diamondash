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
        'poll_interval': '60s'
    }

    @classmethod
    def parse(cls, config):
        if 'name' not in config:
            raise ConfigError('Dashboard name not specified.')

        name = config['name']
        config.setdefault('title', name)
        name = utils.slugify(name)
        config['name'] = name

        # request interval is converted to milliseconds for client side
        config['poll_interval'] = utils.parse_interval(config['poll_interval'])

        if 'widgets' not in config:
            raise ConfigError("Dashboard '%s' has no widgets" % name)

        backend_config = config.pop('backend', {})

        last_row = []
        rows = [{'widgets': last_row}]
        widget_configs = []

        for widget_config in config['widgets']:
            if widget_config == 'newrow':
                last_row = []
                rows.append({'widgets': last_row})
            else:
                widget_config = cls.parse_widget(widget_config, backend_config)
                last_row.append({'name': widget_config['name']})
                widget_configs.append(widget_config)

        config['rows'] = rows
        config['widgets'] = widget_configs

        return config

    @classmethod
    def parse_widget(cls, config, backend_config):
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

    loader = XMLString(
        resource_string(__name__, 'views/dashboard.xml'))

    def __init__(self, config):
        self.config = config

        self.widgets = []
        self.widgets_by_name = {}

        for widget in self.config['widgets']:
            self.add_widget(widget, add_to_layout=False)

    def add_widget(self, config, add_to_layout=True):
        """Adds a widget to the dashboard. """
        type_cls = utils.load_class_by_string(config['type'])
        widget = type_cls(config)

        self.widgets_by_name[config['name']] = widget
        self.widgets.append(widget)

        if add_to_layout:
            last_row = self.config['rows'][-1]
            last_row['widgets'].append({'name': config['name']})

    def get_widget(self, name):
        """Returns a widget using the passed in widget name."""
        return self.widgets_by_name.get(name, None)

    def get_details(self):
        """Returns data describing the dashboard."""
        details = self.config.copy()
        details['widgets'] = [w.get_details() for w in self.widgets]
        return details

    @renderer
    def init_script_renderer(self, request, tag):
        tag.fillSlots(config_slot=json.dumps(self.get_details()))
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
        href = '#' if self.shared else '/'
        tag.fillSlots(brand_href_slot=href)
        return tag

    @renderer
    def dashboard_container_renderer(self, request, tag):
        return self.dashboard
