"""Web app for displaying dashboard components sourced from Graphite data"""

from klein import resource, route
from twisted.web.client import getPage
from twisted.web.template import Element, renderer, XMLFile
from twisted.web.static import File
from twisted.python import log

# TODO load from args
graphite_url = "http://127.0.0.1:8000"

class DashboardElement(Element):
    """Loads dashboard template"""

    loader = XMLFile('templates/dashboard.xml')

    def __init__(self, config_filename):
        self.widget_configuration = {}
        self._read_config_file(config_filename)

    def _read_config_file(self, config_filename):
        """Loads dashboard information from a config file"""
        # TODO load from config file
        self.widget_configs = {
            #'random_count_sum': {
            'vumi.random.count.sum': { # will be removed soon
                'title': 'Sum of random count',
                'type': 'graph',
                'metric': 'vumi.random.count.sum',
                'width': '300px',
                'height': '150px'
            },
            #'random_timer_average': {
            'vumi.random.timer.avg': { # will be removed soon
                'title': 'Average of random timer',
                'type': 'graph',
                'metric': 'vumi.random.timer.avg'
            }
        }

    @renderer
    def widget(self, request, tag):
        for widget_name, widget_config in self.widget_configs.items():
            new_tag = tag.clone()
            widget_class_attr = 'widget'
            widget_style_attr = ''

            # TODO use graph as default type
            if widget_config['type'] == 'graph':
                widget_class_attr += ' graph'

            if 'width' in widget_config:
                widget_style_attr += 'width: ' + widget_config['width'] + '; '

            if 'height' in widget_config:
                widget_style_attr += 'height: ' + widget_config['height'] + '; '

            new_tag.fillSlots(widget_title_slot=widget_config['title'],
                              widget_style_slot=widget_style_attr,
                              widget_class_slot=widget_class_attr,
                              widget_id_slot=widget_name)
            yield new_tag


@route('/static/')
def static(request):
    """Routing for all static files (css, js)"""
    return File("./static")


@route('/')
def show_index(request):
    """Routing for homepage"""
    return DashboardElement('./etc/dashboard.yml')


def format_render_results(results):
    """
    Formats the json output received from graphite on response from a render
    request into something usable from the client side
    """
    # TODO


def construct_render_url(request):
    """Constructs the graphite render url based on the client's request uri"""
    uri = request.uri['/render/'.length:]
    # TODO


@route('/render/')
def render(request):
    """Routing for client render request"""
    #render_url = construct_render_url(request)
    render_url = graphite_url + request.uri
    d = getPage(render_url)
    #d.addCallback(format_render_results)
    return d
