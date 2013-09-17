# -*- test-case-name: diamondash.tests.test_dashboard -*-

"""Dashboard functionality for the diamondash web app"""

import json
import yaml
from os import path
from glob import glob
from pkg_resources import resource_string, resource_filename

from twisted.web.template import Element, renderer, XMLString

from diamondash import utils, ConfigMixin, ConfigError, PageElement


class Dashboard(Element, ConfigMixin):
    """
    Holds a dashboard's configuration data and widget elements.

    Dashboard instances are created when diamondash starts.
    """

    __DEFAULTS = {'request_interval': '60s'}
    __CONFIG_TAG = 'diamondash.dashboard.Dashboard'

    DEFAULT_TEMPLATE_FILEPATH = resource_filename(
        __name__, 'views/dashboard_container.xml')
    DEFAULT_REQUEST_INTERVAL = '60s'
    LAYOUT_FUNCTIONS = {'newrow': '_new_row'}

    # the max number of columns allowed by Bootstrap's grid system
    MAX_WIDTH = 12

    def __init__(self, name, title, client_config, share_id=None, widgets=[],
                 template_filepath=None):
        self.name = name
        self.title = title
        self.share_id = share_id

        self.client_config = client_config
        self.client_config.setdefault('widgets', [])

        self.widgets = []
        self.widgets_by_name = {}
        self.last_row = WidgetRow()
        self.rows = [self.last_row]

        self.stylesheets = set()
        self.javascripts = set()

        template_filepath = template_filepath
        if template_filepath is None:
            template_filepath = self.DEFAULT_TEMPLATE_FILEPATH
        self.loader = XMLString(open(template_filepath).read())

        for widget in widgets:
            self.add_widget(widget)

    @classmethod
    def parse_config(cls, config, class_defaults={}):
        """Parses a Dashboard config."""
        class_defaults = cls.override_class_defaults(
            class_defaults, config.pop('defaults', {}))
        defaults = class_defaults.get(cls.__CONFIG_TAG, {})
        config = utils.update_dict(cls.__DEFAULTS, defaults, config)

        name = config.get('name', None)
        if name is None:
            raise ConfigError('Dashboard name not specified.')

        config.setdefault('title', name)
        name = utils.slugify(name)
        config['name'] = name
        config['share_id'] = config.get('share_id')

        # request interval is converted to milliseconds for client side
        config['client_config'] = {
            'name': name,
            'requestInterval': (
                utils.parse_interval(config.pop('request_interval')) * 1000),
        }

        if 'widgets' not in config:
            raise ConfigError('Dashboard %s does not have any widgets' % name)

        widgets = []
        for widget_config in config['widgets']:
            if (isinstance(widget_config, str) and
                widget_config in cls.LAYOUT_FUNCTIONS):
                widgets.append(widget_config)
            else:
                widget_type = widget_config.pop('type', None)
                widget_class = utils.load_class_by_string(widget_type)
                widget = widget_class.from_config(
                    widget_config, class_defaults)
                widgets.append(widget)
        config['widgets'] = widgets

        return config

    @classmethod
    def from_config_file(cls, filename, class_defaults=None):
        """Loads dashboard config from a config file"""
        try:
            config = yaml.safe_load(open(filename))
        except IOError:
            raise ConfigError('File %s not found.' % (filename,))

        return cls.from_config(config, class_defaults)

    @classmethod
    def dashboards_from_dir(cls, dashboards_dir, class_defaults={}):
        """Creates a list of dashboards from a config dir"""

        dashboards = []
        for filepath in glob(path.join(dashboards_dir, "*.yml")):
            dashboard = Dashboard.from_config_file(filepath, class_defaults)
            dashboards.append(dashboard)

        return dashboards

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

            # append to the last row
            self.last_row.add_widget(WidgetContainer(widget))

    def get_widget(self, name):
        """Returns a widget using the passed in widget name."""
        return self.widgets_by_name.get(name, None)

    def get_details(self):
        """Returns data describing the dashboard."""
        return {
            'title': self.title,
            'share_id': self.share_id,
            'widgets': [widget.get_details() for widget in self.widgets]
        }

    def apply_layout_fn(self, name):
        return getattr(self, self.LAYOUT_FUNCTIONS[name])()

    @renderer
    def dashboard_title_renderer(self, request, tag):
        return tag(self.title)

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
        self.width = widget.width
        span_class = "col-md-%s" % widget.width
        self.classes = " ".join(('widget', widget.TYPE_NAME, span_class))

    @renderer
    def widget_renderer(self, request, tag):
        widget = self.widget
        tag.fillSlots(id_slot=widget.name,
                      class_slot=self.classes,
                      title_slot=widget.title,
                      widget_slot=widget)
        return tag


class DashboardPage(PageElement):
    """
    An element for displaying an actual dashboard page.

    DashboardPage instances are created on page request.
    """

    loader = XMLString(resource_string(__name__, 'views/dashboard_page.xml'))

    def __init__(self, dashboard):
        self.dashboard = dashboard

    @renderer
    def brand_renderer(self, request, tag):
        href = '' if self.dashboard.share_id is not None else '/'
        tag.fillSlots(brand_href_slot=href)
        return tag

    @renderer
    def dashboard_container_renderer(self, request, tag):
        return self.dashboard
