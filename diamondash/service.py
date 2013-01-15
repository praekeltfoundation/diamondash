from twisted.web import server
from twisted.python import usage
from twisted.application import service, strports

import diamondash.server as webserver

DEFAULT_PORT = '8080'
DEFAULT_CONFIG_DIR = 'etc'


class Options(usage.Options):
    """Command line args when run as a twistd plugin"""
    # TODO other args
    optParameters = [["port", "p", DEFAULT_PORT,
                      "Port number for diamondash to listen on"],
                     ["config_dir", "c", DEFAULT_CONFIG_DIR,
                      "Config dir"]]


def makeService(options):
    #webserver.configure(options['config_dir'])
    diamondash_service = service.MultiService()
    site = server.Site(webserver.resource())
    strports_service = strports.service(options['port'], site)
    strports_service.setServiceParent(diamondash_service)
    return diamondash_service
