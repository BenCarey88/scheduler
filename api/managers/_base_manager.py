"""Base manager classes for others to inherit from."""


class ManagerError(Exception):
    """Base error class for manager exceptions."""


def require_class(require_class, raise_error=False):
    """Decorator factory to check object is a specific class instance.

    Args:
        require_class (class or tuple): the class or classes to
            allow.
        raise_error (bool): if True, raise error for unallowed classes.
            Otherwise just return None. We should raise an error when
            the implementation in the ui should make it impossible for
            this to be run on an unallowed class.

    Returns:
        (function): the decorator function. This decorator will run
            a function that takes in an object as first input but
            raise an error if the object is not one of the designated
            classes.
    """
    def decorator(function):
        def decorated_func(self, object, *args, **kwargs):
            if not isinstance(object, require_class):
                if raise_error:
                    raise ManagerError(
                        "This method requires objects of type {0}, not "
                        "{1}".format(
                            str(require_class),
                            object.__class__.__name__
                        )
                    )
                return None
            return function(self, object, *args, **kwargs)
        return decorated_func
    return decorator


class BaseManager(object):
    """Base manager class that all others inherit from."""
    def __init__(self, user_prefs, name="", suffix="manager"):
        """Initialize class.

        Args:
            name (str): name of manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            suffix (str): string to append to name.
        """
        if suffix and name:
            self._name = "{0}_{1}".format(name, suffix)
        elif name:
            self._name = name
        else:
            self._name = suffix
        self._project_user_prefs = user_prefs
