from twisted.web.template import renderer

from diamondash.widgets.widget.widget import Widget


class TextWidget(Widget):
    """A widget that simply displays static text."""

    TEMPLATE = 'text/template.xml'
    STYLESHEETS = ('text/style.css',)

    def __init__(self, name, title, text):
        super(TextWidget, self).__init__(name, title)
        self.text = text

    @renderer
    def text_renderer(self, request, tag):
        return tag(self.text)
