import re
import sys
from os import path
from datetime import datetime
from unidecode import unidecode

PUNCT_RE = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
NUMBER_SUFFIXES = ['', 'K', 'M', 'B', 'T']
EPS = 0.0001


def isint(n):
    """
    Checks if a number is equivalent to an integer value
    """
    if isinstance(n, (int, long)):
        return True

    return abs(n - int(n)) <= EPS


def format_value(n):
    mag = 0
    if abs(n) < 1000:
        return (str(int(n)) if isint(n)
                else '%.3f' % (n,))
    while abs(n) >= 1000 and mag < len(NUMBER_SUFFIXES) - 1:
        mag += 1
        n /= 1000.0
    return '%.3f%s' % (n, NUMBER_SUFFIXES[mag])


def format_time(time):
    # convert and cut of seconds
    time = str(datetime.utcfromtimestamp(time))[:-3]
    return time


def slugify(text):
    """Slugifies the passed in text"""
    result = []
    for word in PUNCT_RE.split(text.lower()):
        result.extend(unidecode(word).split())
    return '-'.join(result)


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
    parts = class_path.split('.')
    module_name = '.'.join(parts[:-1])
    class_name = parts[-1]
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
