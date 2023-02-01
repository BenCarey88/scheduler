"""Base manager classes for others to inherit from."""

from scheduler.api.tree.base_task_item import BaseTaskItem
from scheduler.api.tree.task import Task
from scheduler.api.tree.task_category import TaskCategory


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
    def __init__(self, user_prefs, filterer, name="", suffix="manager"):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            filterer (Filterer): filterer class for storing filters.
            name (str): name of manager.
            suffix (str): string to append to name.
        """
        if suffix and name:
            self._name = "{0}_{1}".format(name, suffix)
        elif name:
            self._name = name
        else:
            self._name = suffix
        self._project_user_prefs = user_prefs
        self._filterer = filterer

    def clear_filter_caches(self):
        """Clear all filter caches."""
        self._filterer.clear_filter_caches()

    @require_class(BaseTaskItem, raise_error=True)
    def is_task(self, item):
        """Check if tree item is task.

        Args:
            item (BaseTaskItem): tree item to check.

        Return:
            (bool): whether or not item is task.
        """
        return isinstance(item, Task)

    @require_class(BaseTaskItem, raise_error=True)
    def is_task_category(self, item):
        """Check if tree item is task category.

        Args:
            item (BaseTaskItem): tree item to check.

        Return:
            (bool): whether or not item is task category.
        """
        return isinstance(item, TaskCategory)


class BaseCalendarManager(BaseManager):
    """Base manager for all calendar classes."""
    def __init__(
            self,
            user_prefs,
            calendar,
            tree_manager,
            filterer,
            name="",
            suffix="manager"):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
            filterer (Filterer): filterer class for storing filters.
            name (str): manager name.
            suffix (str): string to append to name.
        """
        self._tree_manager = tree_manager
        self._calendar = calendar
        super(BaseCalendarManager, self).__init__(
            user_prefs,
            filterer=filterer,
            name=name,
            suffix=suffix,
        )

    @property
    def calendar(self):
        """Get calendar object.

        Returns:
            (Calendar): calendar object.
        """
        return self._calendar

    @property
    def tree_root(self):
        """Get tree root object.

        Returns:
            (TaskRoot): tree root object.
        """
        return self.calendar.task_root
