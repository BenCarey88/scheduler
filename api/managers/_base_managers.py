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
    def __init__(self, name, user_prefs):
        """Initialize class.

        Args:
            name (str): name of manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
        """
        self._name = name
        self._project_user_prefs = user_prefs


class BaseTreeManager(object):
    """Base tree manager class to build tree manager classes from."""
    def __init__(self, name, user_prefs, tree_root, archive_tree_root):
        """Initialize class.

        Args:
            name (str): name of tree manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            tree_root (TaskRoot): root task object.
            archive_tree_root (TaskRoot): root archive task object.
        """
        self._tree_root = tree_root
        self._archive_tree_root = archive_tree_root
        super(BaseTreeManager, self).__init__(name, user_prefs)


class BaseCalendarManager(object):
    """Base calendar manager class to build calendar managers from."""
    def __init__(self, name, user_prefs, calendar, archive_calendar):
        """Initialize class.

        Args:
            name (str): name of tree manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            archive_calendar (Calendar): archive calendar object.
        """
        self._calendar = calendar
        self._archive_calendar = archive_calendar
        super(BaseCalendarManager, self).__init__(name, user_prefs, calendar)
