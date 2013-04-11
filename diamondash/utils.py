import re
import sys
import time
from os import path
from math import floor
from unidecode import unidecode

from twisted.internet import reactor
from twisted.web.client import HTTPClientFactory, _parse as parse_url

# The internal representation of intervals in diamondash is seconds.
# This multiplier is used to convert the internal interval representation to
# what is needed by the client side
CLIENT_INTERVAL_MULTIPLIER = 1000  # seconds -> milliseconds

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
    Return integer seconds.
    """
    if not isinstance(interval, basestring):
        # It isn't a string, so there's nothing to parse
        return interval
    suffixes = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
    }
    try:
        for suffix, multiplier in suffixes.items():
            if interval.endswith(suffix):
                return int(interval[:-1]) * multiplier
        return int(interval)
    except ValueError:
        raise ValueError("%r is not a valid time interval.")


def last_dir_in_path(pathname):
    return path.split(path.dirname(pathname))[1]


def update_dict(*dicts):
    """
    Returns a new dict updated with a tuple of dicts.
    """
    new_dict = {}
    for d in dicts:
        new_dict.update(d)
    return new_dict


def now():
    return int(time.time())


def relative_to_now(t):
    return now() + t


def round_time(t, interval):
    i = int(round(t / float(interval)))
    return interval * i


def floor_time(t, interval):
    i = int(floor(t / float(interval)))
    return interval * i


def to_client_interval(t):
    """
    Convert time interval from interal representation to representation used by
    client side
    """
    return t * CLIENT_INTERVAL_MULTIPLIER


class Accessor(object):
    def __init__(self, fallback=None, wrapper=None, **objs):
        lookup = dict(objs)
        lookup['fallback'] = fallback
        self.lookup = lookup
        self.wrapper = wrapper or self._wrapper

    def _wrapper(self, name, obj, *args, **kwargs):
        return obj

    def __call__(self, name, *args, **kwargs):
        obj = self.lookup.get(name, self.lookup['fallback'])
        return self.wrapper(name, obj, *args, **kwargs)


def http_request(url, data=None, headers={}, method='GET'):
    scheme, host, port, path = parse_url(url)
    factory = HTTPClientFactory(
        url,
        postdata=data,
        method=method,
        headers=headers)
    reactor.connectTCP(host, port, factory)

    def got_response(body):
        return {
            'body': body,
            'status': factory.status,
            'headers': factory.response_headers,
        }

    factory.deferred.addCallback(got_response)
    return factory.deferred
