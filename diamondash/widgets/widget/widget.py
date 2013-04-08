from pkg_resources import resource_string

from twisted.web.template import Element
from twisted.web.template import XMLString

from diamondash import utils, ConfigMixin, ConfigError


class Widget(Element, ConfigMixin):
    """Abstract class for dashboard widgets."""

    __DEFAULTS = {}
    __CONFIG_TAG = 'diamondash.widgets.Widget'

    loader = XMLString(resource_string(__name__, 'template.xml'))

    MIN_COLUMN_SPAN = 3
    MAX_COLUMN_SPAN = 12

    # backbone model and view classes
    MODEL = 'WidgetModel'
    VIEW = 'WidgetView'
    TYPE_NAME = "abstract_widget"

    def __init__(self, name, title, client_config, width):
        self.name = name
        self.title = title
        self.client_config = client_config
        self.width = width

    @classmethod
    def parse_config(cls, config, class_defaults={}):
        """Parses a widget config, altering it where necessary."""
        defaults = class_defaults.get(cls.__CONFIG_TAG, {})
        config = utils.update_dict(cls.__DEFAULTS, defaults, config)

        name = config.get('name', None)
        if name is None:
            raise ConfigError('All widgets need a name.')

        name = config['name']
        config.setdefault('title', name)
        name = utils.slugify(name)
        config['name'] = name

        width = config.get('width', None)
        config['width'] = (cls.MIN_COLUMN_SPAN if width is None
                           else cls.parse_width(width))

        config['client_config'] = {
            'model': {'name': name},
            'view': {},
            'modelClass': cls.MODEL,
            'viewClass': cls.VIEW,
        }

        return config

    @classmethod
    def parse_width(cls, width):
        """
        Wraps the passed in width as an int and clamps the value to the width
        range.
        """
        width = int(width)
        width = max(cls.MIN_COLUMN_SPAN, min(width, cls.MAX_COLUMN_SPAN))
        return width

    def get_details(self):
        """Returns data describing the widget."""
        return {'title': self.title, 'type': self.TYPE_NAME}
