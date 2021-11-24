"""Utility functions for scheduler api."""

from collections import OrderedDict
import datetime
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


# TODO: maybe want separate time_utils or even time class
# time class is probably ideal, so we can rely on that to recognise
# the format of the string, and just use to_str and from_str methods
def get_date_time_from_string(datetime_str):
    """Get datetime object from string

    Args:
        datetime_str (str): date_time string in format:
            yyyy-mm-dd hh:mm:ss.ff

    Returns:
        (datetime.datetime): datetime object.
    """
    return  datetime.datetime.strptime(
        datetime_str,
        "%Y-%m-%d %H:%M:%S.%f"
    )


def get_time_from_string(datetime_str):
    """Get datetime time object from string

    Args:
        datetime_str (str): time string in format:
            hh:mm:ss.ff

    Returns:
        (datetime.datetime): datetime object.
    """
    return datetime.datetime.strptime(
        datetime_str,
        "%H:%M:%S.%f"
    )


def get_date_from_string(datetime_str):
    """Get datetime date object from string

    Args:
        datetime_str (str): date string in format:
            yyyy-mm-dd

    Returns:
        (datetime.datetime): datetime object.
    """
    return datetime.datetime.strptime(
        datetime_str,
        "%Y-%m-%d"
    )
