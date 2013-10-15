from pkg_resources import resource_string

from twisted.web.template import Element
from twisted.web.template import XMLString

from diamondash import utils
from diamondash.config import Config, ConfigError


class WidgetConfig(Config):
    TYPE_NAME = 'widget'

    MIN_COLUMN_SPAN = 3
    MAX_COLUMN_SPAN = 12

    DEFAULTS = {
        'type_name': TYPE_NAME,
        'width': MIN_COLUMN_SPAN
    }

    @classmethod
    def parse_width(cls, width):
        """
        Wraps the passed in width as an int and clamps the value to the width
        range.
        """
        width = int(width)
        width = max(cls.MIN_COLUMN_SPAN, min(width, cls.MAX_COLUMN_SPAN))
        return width

    @classmethod
    def parse(cls, config):
        config['type_name'] = cls.TYPE_NAME

        if 'name' not in config:
            raise ConfigError('All widgets need a name.')

        name = config['name']
        config.setdefault('title', name)
        name = utils.slugify(name)
        config['name'] = name

        config['width'] = cls.parse_width(config['width'])

        config['client_config'] = {
            'view': {},
            'model': {'name': name},
            'typeName': cls.TYPE_NAME,
        }

        return config


class Widget(Element):
    """Abstract class for dashboard widgets."""

    loader = XMLString(resource_string(__name__, 'template.xml'))
    CONFIG_CLS = WidgetConfig

    def __init__(self, config):
        self.config = config

    def get_details(self):
        """Returns data describing the widget."""
        return self.config
