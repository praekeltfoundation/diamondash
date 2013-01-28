# -*- test-case-name: diamondash.tests.test_dashboard -*-

"""Dashboard functionality for the diamondash web app"""

import json
import yaml
from os import path
from pkg_resources import resource_string, resource_filename

from twisted.web.template import Element, renderer, XMLString

from exceptions import ConfigError
from diamondash import utils


class Dashboard(Element):
    """
    Holds a dashboard's configuration data and widget elements.

    Dashboard instances are created when diamondash starts.
    """

    DEFAULT_TEMPLATE_FILEPATH = resource_filename(
        __name__, 'templates/dashboard_container.xml')
    DEFAULT_REQUEST_INTERVAL = '60s'
    LAYOUT_FUNCTIONS = {'newrow': '_new_row'}
    WIDGET_STYLESHEETS_PATH = "/public/css/widgets/"
    WIDGET_JAVASCRIPTS_PATH = "widgets/"

    # the max number of columns allowed by Bootstrap's grid system
    MAX_WIDTH = 12

    def __init__(self, name, title, widgets, client_config, share_id=None,
                 template_filepath=None):
        self.name = name
        self.title = title
        self.share_id = share_id

        self.client_config = client_config
        client_config.setdefault('widgets', [])

        self.widgets = []
        self.widgets_by_name = {}
        self.last_row = WidgetRow()
        self.rows = [self.last_row]

        self.stylesheets = set()
        self.javascripts = set()

        if template_filepath is None:
            template_filepath = self.DEFAULT_TEMPLATE_FILEPATH
        self.loader = XMLString(open(template_filepath).read())

        for widget in widgets:
            self.add_widget(widget)

    @classmethod
    def from_config(cls, config):
        """Creates a Dashboard from a config dict."""

        name = config.get('name', None)
        if name is None:
            raise ConfigError('Dashboard name not specified.')

        title = config.get('title', name)
        name = utils.slugify(name)
        share_id = config.get('share_id', None)

        client_config = {}
        client_config['name'] = name
        request_interval = config.get(
            'request_interval', cls.DEFAULT_REQUEST_INTERVAL)

        # parse request interval and convert to milliseconds for client side
        request_interval = utils.parse_interval(request_interval) * 1000

        client_config['requestInterval'] = request_interval

        if 'widgets' not in config:
            raise ConfigError('Dashboard %s does not have any widgets' % name)

        widgets = []
        widget_defaults = config.get('widget_defaults', {})

        for widget_config in config['widgets']:
            if (isinstance(widget_config, str) and
                widget_config in cls.LAYOUT_FUNCTIONS):
                widgets.append(widget_config)
            else:
                widget_type = widget_config.pop('type', None)
                widget_class = utils.load_class_by_string(widget_type)
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

    def _new_row(self):
        self.last_row = WidgetRow()
        self.rows.append(self.last_row)

    def add_widget(self, widget):
        """Adds a widget to the dashboard. """

        if (widget in self.LAYOUT_FUNCTIONS):
            self.apply_layout_fn(widget)
        else:
            if self.last_row.width + widget.width > self.MAX_WIDTH:
                self._new_row()

            self.widgets_by_name[widget.name] = widget
            self.widgets.append(widget)

            self.client_config['widgets'].append(widget.client_config)

            self.stylesheets.update([path.join(self.WIDGET_STYLESHEETS_PATH, s)
                                     for s in widget.STYLESHEETS])

            self.javascripts.update([path.join(self.WIDGET_JAVASCRIPTS_PATH, j)
                                     for j in widget.JAVASCRIPTS])

            # append to the last row
            self.last_row.add_widget(WidgetContainer(widget))

    def get_widget(self, name):
        """Returns a widget using the passed in widget name."""
        return self.widgets_by_name.get(name, None)

    def apply_layout_fn(self, name):
        return getattr(self, self.LAYOUT_FUNCTIONS[name])()

    @renderer
    def stylesheets_renderer(self, request, tag):
        for stylesheet in self.stylesheets:
            yield tag.clone().fillSlots(stylesheet_href_slot=stylesheet)

    @renderer
    def widget_row_renderer(self, request, tag):
        for row in self.rows:
            yield row

    @renderer
    def init_script_renderer(self, request, tag):
        client_config = json.dumps(self.client_config)
        tag.fillSlots(
            javascripts_slot=json.dumps(list(self.javascripts)),
            client_config_slot=client_config)
        return tag


class WidgetRow(Element):
    """
    A row of Widget elements on a dashboard

    WidgetRow instances are created when diamondash starts.
    """

    loader = XMLString(resource_string(__name__, 'templates/widget_row.xml'))

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

    loader = XMLString(
        resource_string(__name__, 'templates/widget_container.xml'))

    def __init__(self, widget):
        self.widget = widget
        self.width = widget.width
        span_class = "span%s" % widget.width
        self.classes = " ".join(('widget', span_class))

    @renderer
    def widget_renderer(self, request, tag):
        widget = self.widget
        tag.fillSlots(id_slot=widget.name,
                      class_slot=self.classes,
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
