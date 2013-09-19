import time
import random

from zope.interface import implements
from twisted.python import usage, log
from twisted.application.internet import TCPClient
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet.task import LoopingCall
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker


class Options(usage.Options):
    optParameters = [
        ['host', 'h', 'localhost', "Carbon's host", str],
        ['port', 'p', 2003, "Carbon's port", int],
        ['interval', 'i', 30, "Interval (seconds) between metric sends", int]]


class MetricSendingClient(LineReceiver):
    def __init__(self, interval, metric_maker=None):
        self.metric_maker = metric_maker or self.maker
        self.interval = interval
        self.periodic_send = LoopingCall(self.send_metrics)

    def connectionMade(self):
        self.start_sending()

    def start_sending(self):
        self.periodic_send.start(self.interval)

    def send_metrics(self):
        log.msg(' * starting sends')

        now = int(time.time())
        metrics = self.metric_maker()

        for name, value in metrics.iteritems():
            line = "%s %s %d" % (name, value, now)
            log.msg('   - sending metric data: "%s"' % line)
            self.sendLine(line)

        log.msg(' * finished sends\n')

    @staticmethod
    def maker():
        return {
            'diamondash.test.small.a.last': random.randint(5, 10),
            'diamondash.test.small.b.last': random.randint(10, 20),
            'diamondash.test.small.c.last': random.randint(0, 20),
            'diamondash.test.small.d.last': random.randint(10, 30),
            'diamondash.test.small.e.last': random.randint(5, 15),

            'diamondash.test.big.a.last': 1000000 * random.randint(5, 10),
            'diamondash.test.big.b.last': 1000000 * random.randint(10, 20),
            'diamondash.test.big.c.last': 1000000 * random.randint(0, 20),
            'diamondash.test.big.d.last': 1000000 * random.randint(10, 30),
            'diamondash.test.big.e.last': 1000000 * random.randint(5, 15),
        }


class MetricSendingClientFactory(ReconnectingClientFactory):
    protocol = MetricSendingClient

    def __init__(self, *client_args):
        self.client_args = client_args

    def buildProtocol(self, addr):
        client = self.protocol(*self.client_args)
        client.factory = self
        self.client = client
        return client


class MetricSendingClientServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "gen_graphite_metrics"
    description = 'Generate graphite metrics'
    options = Options

    def makeService(self, options):
        host, port = options['host'], options['port']
        factory = MetricSendingClientFactory(options['interval'])
        return TCPClient(host, port, factory)
