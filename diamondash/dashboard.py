# -*- test-case-name: diamondash.tests.test_dashboard -*-

"""Dashboard functionality for the diamondash web app"""

import json
import yaml
from os import listdir, path
from pkg_resources import resource_string

from twisted.web.template import Element, renderer, XMLString

from exceptions import ConfigError
from utils import (slugify, parse_interval, load_class_by_string)
from diamondash.widgets.widget import Widget
from diamondash.widgets.graph import GraphWidget


class Dashboard(Element):
    """
    Holds a dashboard's configuration data and widget elements.

    Dashboard instances are created when diamondash starts.
    """

    DEFAULT_REQUEST_INTERVAL = '10s'
    LAYOUT_FUNCTIONS = ['newrow']
    DEFAULT_WIDGET_CLASS = GraphWidget
    WIDGET_STYLESHEETS_PATH = "/public/css/widgets/"

    loader = XMLString(
        resource_string(__name__, 'templates/dashboard_container.xml'))

    def __init__(self, name, title, widgets, client_config, share_id=None):
        self.name = name
        self.title = title
        self.share_id = share_id

        self.client_config = client_config
        client_config.setdefault('widgets', [])

        self.widgets = []
        self.widgets_by_name = {}
        self.rows = [[]]  # init with an empty first row
        self.last_row_width = 0

        self.stylesheets = set()

        self.layoutfns = {
            'newrow': self._new_row
        }

        for widget in widgets:
            self.add_widget(widget)

    def _new_row(self):
        self.rows.append([])
        self.last_row_width = 0

    def add_widget(self, widget):
        """Adds a widget to the dashboard. """

        if (widget in self.LAYOUT_FUNCTIONS):
            layoutfn = self.layoutfns.get(widget, lambda x: x)
            layoutfn()
        else:
            name = widget.name
            self.widgets_by_name[name] = widget
            self.widgets.append(widget)

            self.last_row_width += widget.width
            if self.last_row_width > Widget.MAX_COLUMN_SPAN:
                self._new_row()
                self.last_row_width = widget.width

            self.rows[-1].append(widget)  # append to the last row

            self.client_config['widgets'].append(widget.client_config)

            self.stylesheets.update([path.join(self.WIDGET_STYLESHEETS_PATH, s)
                                     for s in widget.STYLESHEETS])

    def get_widget(self, name):
        """Returns a widget using the passed in widget name"""
        return self.widgets_by_name.get(name, None)

    @classmethod
    def dashboards_from_dir(cls, dir, defaults=None):
        """Creates a list of dashboards from a config dir"""
        dashboards = []

        for filename in listdir(dir):
            filepath = path.join(dir, filename)
            dashboard = Dashboard.from_config_file(filepath, defaults)
            dashboards.append(dashboard)

        return dashboards

    @classmethod
    def from_config(cls, config):
        """
        Parses a dashboard config, applying changes
        where appropriate and returning the resulting config
        """

        name = config.get('name', None)
        if name is None:
            raise ConfigError('Dashboard name not specified.')

        title = config.get('title', name)
        name = slugify(name)
        share_id = config.get('share_id', None)

        client_config = {}
        request_interval = config.get(
            'request_interval', cls.DEFAULT_REQUEST_INTERVAL)
        request_interval = parse_interval(request_interval) * 1000
        client_config['requestInterval'] = request_interval

        if 'widgets' not in config:
            raise ConfigError('Dashboard %s does not have any widgets' % name)

        widget_defaults = config.setdefault('widget_defaults', {})

        widgets = []
        for widget_config in config['widgets']:
            if (widget_config in cls.LAYOUT_FUNCTIONS):
                widgets.append(widget_config)
            else:
                type = widget_config.pop('type', None)
                widget_class = (cls.DEFAULT_WIDGET_CLASS if type is None
                                else load_class_by_string(type))
                widget = widget_class.from_config(widget_config,
                                                  widget_defaults)
                widgets.append(widget)

        return cls(name, title, widgets, client_config, share_id)

    @classmethod
    def from_config_file(cls, filename, defaults=None):
        """Loads dashboard config from a config file"""
        # TODO check and test for invalid config files

        config = {}
        if defaults is not None:
            config.update(defaults)

        try:
            config.update(yaml.safe_load(open(filename)))
        except IOError:
            raise ConfigError('File %s not found.' % (filename,))

        return cls.from_config(config)

    @classmethod
    def from_args(cls, **kwargs):
        """Loads dashboard config from args"""

        config = {}
        if kwargs is not None:
            config.update(kwargs)

        config = cls.parse_config(config)
        return cls.from_config(kwargs)

    @renderer
    def stylesheets_renderer(self, request, tag):
        for stylesheet in self.stylesheets:
            yield tag.clone().fillSlots(stylesheet_href_slot=stylesheet)

    @renderer
    def widget_row_renderer(self, request, tag):
        for row in self.rows:
            yield WidgetRow(row)

    @renderer
    def init_script_renderer(self, request, tag):
        client_config = json.dumps(self.client_config)
        tag.fillSlots(client_config_slot=client_config)
        return tag


class WidgetRow(Element):
    """
    A row of Widget elements on a dashboard

    WidgetRow instances are created on page request.
    """

    loader = XMLString(resource_string(__name__, 'templates/widget_row.xml'))

    def __init__(self, widgets):
        self.widgets = widgets

    @renderer
    def widget_renderer(self, request, tag):
        for widget in self.widgets:
            contained_widget = WidgetContainer(widget)
            yield contained_widget


class WidgetContainer(Element):
    """
    Widget container element holding a widget element.

    WidgetContainer instances are created on page request.
    """

    loader = XMLString(
        resource_string(__name__, 'templates/widget_container.xml'))

    def __init__(self, widget):
        self.widget = widget
        self.span_class = "span%s" % widget.width

    @renderer
    def widget_renderer(self, request, tag):
        widget = self.widget
        tag.fillSlots(id_slot=widget.name,
                      span_class_slot=self.span_class,
                      title_slot=widget.title,
                      widget_slot=widget)
        return tag


class DashboardPage(Element):
    """
    An element for displaying an actual dashboard page.

    DashboardPage instances are created on page request.
    """

    loader = XMLString(resource_string(__name__,
                                       'templates/dashboard_page.xml'))

    def __init__(self, dashboard, is_shared):
        self.dashboard = dashboard
        self.is_shared = is_shared

    @renderer
    def brand_renderer(self, request, tag):
        href = '' if self.is_shared else '/'
        tag.fillSlots(brand_href_slot=href)
        return tag

    @renderer
    def dashboard_name_renderer(self, request, tag):
        return tag(self.dashboard.title)

    @renderer
    def dashboard_container_renderer(self, request, tag):
        return self.dashboard
