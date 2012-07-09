from twisted.web import server, static
from twisted.python import usage
from twisted.application import internet, service, strports

import diamondash.server

webserver = diamondash.server
class Options(usage.Options):
    """Command line args when run as a twistd plugin"""
    # TODO other args
    optParameters = [["port", "p", webserver.DEFAULT_PORT, 
                      "Port number for diamondash to listen on"], 
                     ["config_dir", "c", webserver.DEFAULT_CONFIG_DIR, 
                      "Config dir"],
                     ["graphite_url", "g", webserver.DEFAULT_CONFIG_DIR, 
                      "Graphite URL"]]

def makeService(options):
    webserver.config = webserver.build_config(options)

    s = service.MultiService()
    root = webserver.resource()
    site = server.Site(root)
    strports.service(options['port'], site).setServiceParent(s)

    return s

