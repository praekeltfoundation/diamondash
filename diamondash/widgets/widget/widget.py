from pkg_resources import resource_string

from twisted.web.template import Element
from twisted.web.template import XMLString

from diamondash import utils, ConfigMixin, ConfigError, NotImplementedError


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

    def __init__(self, **kwargs):
        self.name = kwargs['name']
        self.title = kwargs['title']
        self.client_config = kwargs['client_config']
        self.width = kwargs['width']
        self.backends = kwargs.get('backends')

    @classmethod
    def parse_config(cls, config, class_defaults={}):
        """Parses a widget config, altering it where necessary."""
        config = cls.setdefaults(config, class_defaults)

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

    def handle_render_request(self, request):
        """
        Handles a 'render' request from the client, where `params` are the
        request parameters.
        """
        raise NotImplementedError()
