import os

# Twisted Imports
from twisted.web import server, static, twcgi, script, demo, distrib, wsgi
from twisted.internet import interfaces, reactor
from twisted.python import usage, reflect, threadpool
from twisted.spread import pb
from twisted.application import internet, service, strports
from twisted.application.service import ServiceMaker

import diamondash

DEFAULT_STRPORT = 'tcp:8000'

class Options(usage.Options):
    optParameters = [["port", "p", 1235, "The port number to listen on."]]

def makeService(options):
    s = service.MultiService()
    root = diamondash.server.resource
    site = server.Site(root)
    strports.service(8118, site).setServiceParent(s)

    return s

serviceMaker = ServiceMaker('diamondash', 'diamondash_plugin', 'diamondash', 'diamondash')
