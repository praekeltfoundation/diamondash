import re
import sys
from os import path
from time import time
from unidecode import unidecode

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
    text = unidecode(text).lower()
    segments = _punct_re.split(text)
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


def time_from_now(t):
    return int(time()) - t


class Accessor(object):
    def __init__(self, fallback=None, **objs):
        self.objs = objs
        self.fallback = fallback

    def __call__(self, name):
        return self.objs.get(name, self.fallback)
