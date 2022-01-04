"""Utility functions for scheduler api."""

from collections import OrderedDict
import sys


def catch_exceptions(exceptions=None):
    """Decorator factory to make a function safe from the given exceptions.

    The decorated function will return None if the exception occurs, otherwise
    it will return whatever the function would return normally.

    Args:
        exceptions (Exception or tuple(Exception) or None): exception(s) to
            catch. If None, we catch all exceptions.

    Returns:
        (function): the function decorator.
    """
    def decorator(function):
        def decorated_function(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except (exceptions or Exception):
                return None
        return decorated_function
    return decorator


def add_key_at_start(ordered_dict, key, value):
    """Add key to the start of an ordered dict.

    Args:
        ordered_dict (OrderedDict): the ordered dict to add to.
        key (variant): the key to add.
        value (variant): the value to set at that key.
    """
    ordered_dict[key] = value
    if sys.version_info >= (3, 2):
        ordered_dict.move_to_end(key, last=False)
    else:
        for i in range(len(ordered_dict) - 1):
            k, v = ordered_dict.popitem(last=False)
            ordered_dict[k] = v
