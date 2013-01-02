from twisted.web import server
from twisted.python import usage
from twisted.application import service, strports

import diamondash.server as webserver


class Options(usage.Options):
    """Command line args when run as a twistd plugin"""
    # TODO other args
    optParameters = [["port", "p", webserver.DEFAULT_PORT,
                      "Port number for diamondash to listen on"],
                     ["config_dir", "c", webserver.DEFAULT_CONFIG_DIR,
                      "Config dir"]]


def makeService(options):
    webserver.configure(options)

    s = service.MultiService()
    site = server.Site(webserver.root)
    strports.service(options['port'], site).setServiceParent(s)

    return s
