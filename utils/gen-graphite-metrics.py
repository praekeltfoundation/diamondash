#!/usr/bin/env python

import time
import random

from twisted.python import usage
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from twisted.internet.task import LoopingCall


class Options(usage.Options):
    optParameters = [
        ['host', 'h', 'localhost', "Carbon's host", str],
        ['port', 'p', 2003, "Carbon's port", int],
        ['interval', 'i', 30, "Interval (seconds) between metric sends", int]]


class MetricSendingClient(LineReceiver):
    def __init__(self, metric_maker, interval):
        self.metric_maker = metric_maker
        self.interval = interval
        self.periodic_send = LoopingCall(self.send_metrics)

    def connectionMade(self):
        self.start_sending()

    def start_sending(self):
        self.periodic_send.start(self.interval)

    def send_metrics(self):
        print ' * starting sends'

        now = int(time.time())
        metrics = self.metric_maker()

        for name, value in metrics.iteritems():
            line = "%s %s %d" % (name, value, now)
            print '   * sending metric data: "%s"' % line
            self.sendLine(line)

        print ' * finished sends\n'


class MetricSendingClientFactory(ReconnectingClientFactory):
    protocol = MetricSendingClient

    def __init__(self, *client_args):
        self.client_args = client_args

    def buildProtocol(self, addr):
        client = self.protocol(*self.client_args)
        client.factory = self
        self.client = client
        return client


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


def main(argv):
    options = Options()
    options.parseOptions(argv)

    factory = MetricSendingClientFactory(maker, options['interval'])
    reactor.connectTCP(options['host'], options['port'], factory)
    reactor.run()


if __name__ == '__main__':
    import sys

    exit(main(sys.argv[1:]))
