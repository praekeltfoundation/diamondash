from twisted.web import server
from twisted.python import usage
from twisted.application import service, strports

from diamondash.server import DiamondashConfig, DiamondashServer

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
    config = DiamondashConfig.from_dir(options['config_dir'])
    diamondash = DiamondashServer(config)

    site = server.Site(diamondash.app.resource())
    diamondash_service = service.MultiService()
    strports_service = strports.service(options['port'], site)
    strports_service.setServiceParent(diamondash_service)

    return diamondash_service
