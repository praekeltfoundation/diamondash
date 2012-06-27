"""Web app for displaying dashboard components sourced from Graphite data"""

from klein import resource, route
from twisted.web.client import getPage
from twisted.web.template import Element, renderer, XMLFile
from twisted.web.static import File
from twisted.python import log

# TODO load from args
_graphite_url = "http://127.0.0.1:8000"


class DashboardElement(Element):
    """Loads dashboard template"""

    loader = XMLFile('templates/dashboard.xml')

    def __init__(self, config_filename):
        self.widget_configuration = {}
        self.read_config_file(config_filename)

    def read_config_file(self, config_filename):
        """Loads dashboard information from a config file"""
        # TODO load from config file
        self.widget_configs = {
            'random_count_sum': {
                'type': 'graph',
                'metric': 'vumi.random.count.sum'
            },
            'random_timer_average': {
                'type': 'graph',
                'metric': 'vumi.random.timer.avg'
            }
        }

    @renderer
    def widget(self, request, tag):
        for widget_name, widget_config in self.widget_configs.items():
            new_tag = tag.clone()
            widget_class_attr = 'widget'

            if (widget_config['type'] == 'graph'):
                widget_class_attr += ' graph'

            new_tag.fillSlots(widget_name_slot=widget_name,
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


#def _get_data():
#    """"""
    # TODO


@route('/render/')
def redirect_render(request):
    """Async redirection of render request to graphite"""
    render_url = _graphite_url + request.uri
    return getPage(render_url)
