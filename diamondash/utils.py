import re
import sys
import time
from os import path
from unidecode import unidecode
from urlparse import urlparse
from math import floor

from twisted.internet import reactor
from twisted.web.client import HTTPClientFactory

_punct_re = re.compile(r'[^a-zA-Z0-9]+')
_number_suffixes = ['', 'K', 'M', 'B', 'T']
_eps = 0.0001


def isint(n):
    """
    Checks if a number is equivalent to an integer value
    """
    if isinstance(n, (int, long)):
        return True

    return abs(n - int(n)) <= _eps


def slugify(text):
    """Slugifies the passed in text"""
    if isinstance(text, unicode):
        text = unidecode(text)
    segments = _punct_re.split(text.lower())
    return '-'.join(word for segment in segments for word in segment.split())


def import_module(name):
    """
    It's here so that we can avoid using importlib and not have to
    juggle different deps between Python versions.
    """
    __import__(name)
    return sys.modules[name]


def load_class(module_name, class_name):
    """
    Load a class when given its module and its class name.
    """
    mod = import_module(module_name)
    return getattr(mod, class_name)


def load_class_by_string(class_path):
    """
    Load a class when given its full name, including modules in python
    dot notation.
    """
    module_name, class_name = class_path.rsplit('.', 1)
    return load_class(module_name, class_name)


def parse_interval(interval):
    """
    Recognise 's', 'm', 'h', 'd' suffixes as seconds, minutes, hours and days.
    Return integer in milliseconds (diamondash's internal time format).
    """
    if not isinstance(interval, basestring):
        # It isn't a string, so there's nothing to parse
        return interval
    suffixes = {
        's': 1000,
        'm': 60000,
        'h': 3600000,
        'd': 86400000,
    }
    try:
        for suffix, multiplier in suffixes.items():
            if interval.endswith(suffix):
                return int(interval[:-1]) * multiplier
        return int(interval)
    except ValueError:
        raise ValueError("%r is not a valid time interval." % interval)


def last_dir_in_path(pathname):
    return path.split(path.dirname(pathname))[1]


def add_dicts(*dicts):
    """
    Returns a new dict updated with a tuple of dicts.
    """
    new_dict = {}
    for d in dicts:
        new_dict.update(d)
    return new_dict


def now():
    return int(time.time()) * 1000


def relative_to_now(t):
    return now() + t


def absolute_time(t):
    return relative_to_now(t) if t < 0 else t


def http_request(url, data=None, headers={}, method='GET'):
    parsed_url = urlparse(url)
    factory = HTTPClientFactory(
        url,
        postdata=data,
        method=method,
        headers=headers)
    reactor.connectTCP(parsed_url.hostname, parsed_url.port, factory)

    def got_response(body):
        return {
            'body': body,
            'status': factory.status,
            'headers': factory.response_headers,
        }

    factory.deferred.addCallback(got_response)
    return factory.deferred


def floor_time(t, interval, relative_to=None):
    offset = relative_to % interval if relative_to is not None else 0
    i = int(floor((t - offset) / float(interval)))
    return max(offset + (i * interval), 0)


def round_time(t, interval, relative_to=None):
    offset = relative_to % interval if relative_to is not None else 0
    i = int(round((t - offset) / float(interval)))
    return max(offset + (i * interval), 0)


time_aligners = {
    'round': round_time,
    'floor': floor_time,
}
