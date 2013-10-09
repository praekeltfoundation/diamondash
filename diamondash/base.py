from pkg_resources import resource_string

from twisted.web.template import Element, renderer, XMLString


class ResourcesElement(Element):
    loader = XMLString(resource_string(__name__, 'views/resources.xml'))


class PageElement(Element):
    @renderer
    def resources_renderer(self, request, tag):
        return ResourcesElement()
