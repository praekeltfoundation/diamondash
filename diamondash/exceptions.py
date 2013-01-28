"""Exceptions for diamondash"""


class ConfigError(Exception):
    """Raised when there is an error parsing a configuration"""


class NotImplementedError(Exception):
    """
    Raised when a subclass has not implemented a method of it's abstract
    parent class
    """
