from twisted.web import server
from twisted.python import usage
from twisted.application import service, strports

from diamondash.server import DiamondashServer

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
    srv = DiamondashServer.from_config_dir(options['config_dir'])
    diamondash_service = service.MultiService()
    site = server.Site(srv.app.resource())
    strports_service = strports.service(options['port'], site)
    strports_service.setServiceParent(diamondash_service)
    return diamondash_service
