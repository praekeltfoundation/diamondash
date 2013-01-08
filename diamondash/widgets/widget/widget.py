from pkg_resources import resource_string

from twisted.web.template import Element, XMLString


class Widget(Element):
    """
    Abstract class for dashboard widgets.
    """

    TEMPLATE = None
    CLIENT_DEPS = {
        'modules': ['widget'],
        'stylesheets': [],
        'model': 'widget.WidgetModel',
        'view': 'widget.WidgetView',
    }

    def __init__(self, name, title):
        self.name = name
        self.title = title
        if self.TEMPLATE is not None:
            self.loader = XMLString(resource_string(__name__, self.TEMPLATE))

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

    def handle_request(self, **params):
        """
        Handles a request from the client, where `params` are the request
        parameters.
        """
        pass
