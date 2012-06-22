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


@route('/static/')
def static(request):
    """Routing for all static files (css, js)"""
    return File("./static")


@route('/')
def show_index(request):
    """Routing for homepage"""
    return DashboardElement()


@route('/render/')
def redirect_render(request):
    """Async redirection of render request to graphite"""
    render_url = _graphite_url + request.uri
    return getPage(render_url)
