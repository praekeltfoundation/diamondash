from pkg_resources import resource_string

from twisted.web.template import renderer, XMLString

from diamondash.widgets.widget.widget import Widget


class TextWidget(Widget):
    """A widget that simply displays static text."""

    loader = XMLString(resource_string(__name__, 'template.xml'))

    MIN_COLUMN_SPAN = 2
    STYLESHEETS = ('text/style.css',)

    def __init__(self, **kwargs):
        super(TextWidget, self).__init__(**kwargs)
        self.text = kwargs['text']

    @renderer
    def text_renderer(self, request, tag):
        return tag(self.text)
