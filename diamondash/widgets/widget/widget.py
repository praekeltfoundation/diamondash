from twisted.web.template import Element


class Widget(Element):
    """Abstract class for dashboard widgets."""

    loader = None
    STYLESHEETS = ()
    JAVASCRIPTS = ('widget/widget.js',)
    MODEL = 'WidgetModel'
    VIEWS = 'WidgetView'
    MAX_COLUMN_SPAN = 4

    def __init__(self, name, title, client_config, width=1):
        self.name = name
        self.title = title
        self.client_config = client_config
        self.width = width

    @classmethod
    def parse_width(cls, width):
        """
        Wraps the passed in width as an int and
        clamps the value to the width range
        """
        width = int(width)
        width = max(1, min(width, cls.MAX_COLUMN_SPAN))
        return width

    @classmethod
    def parse_config(cls, config):
        """
        Parses a widget config, altering it where necessary
        """
        name = config['name']
        config.setdefault('title', name)
        return config

    @classmethod
    def from_config(cls, config):
        """
        Parses a widget config, then returns the constructed widget
        """
        config = cls.parse_config(config)
        return cls(**config)

    def handle_render_request(self, **params):
        """
        Handles a 'render' request from the client, where `params` are the
        request parameters.
        """
        pass


class GraphiteWidget(Widget):
    """Abstract widget that obtains metric data from graphite."""
