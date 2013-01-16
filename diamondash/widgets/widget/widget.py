from twisted.web.template import Element

from diamondash.utils import slugify
from diamondash.exceptions import ConfigError


class Widget(Element):
    """Abstract class for dashboard widgets."""

    loader = None
    STYLESHEETS = ()
    JAVASCRIPTS = ('widget/widget.js',)
    MODEL = 'WidgetModel'
    VIEW = 'WidgetView'
    MAX_COLUMN_SPAN = 4

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.title = kwargs['title']
        self.client_config = kwargs['client_config']
        self.width = kwargs['width']

    @classmethod
    def parse_width(cls, width):
        """
        Wraps the passed in width as an int and clamps the value to the width
        range.
        """
        width = int(width)
        width = max(1, min(width, cls.MAX_COLUMN_SPAN))
        return width

    @classmethod
    def parse_config(cls, config):
        """Parses a widget config, altering it where necessary."""

        name = config.get('name', None)
        if name is None:
            raise ConfigError('Widget name not specified.')

        config.pop('type')

        name = config['name']
        config.setdefault('title', name)
        config['name'] = slugify(name)

        width = config.get('width', None)
        config['width'] = 1 if width is None else cls.parse_width(width)

        config['client_config'] = {
            'model': cls.MODEL,
            'view': cls.VIEW,
        }

        return config

    @classmethod
    def from_config(cls, config, defaults):
        """Parses a widget config, then returns the constructed widget."""
        config = cls.parse_config(config)
        return cls(**config)

    def handle_render_request(self, **params):
        """
        Handles a 'render' request from the client, where `params` are the
        request parameters.
        """
        return {}
