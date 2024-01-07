"""Base manager classes for others to inherit from."""

from scheduler.api.filter import quasiconvert_filter
from scheduler.api.tree import BaseTaskItem, Task, TaskCategory


class ManagerError(Exception):
    """Base error class for manager exceptions."""


def require_class(require_class, raise_error=False, return_val=False):
    """Decorator factory to check object is a specific class instance.

    Args:
        require_class (class or tuple): the class or classes to
            allow.
        raise_error (bool): if True, raise error for unallowed classes.
            Otherwise return return_val. We should raise an error when
            the implementation in the ui should make it impossible for
            this to be run on an unallowed class.
        return_val (variant): value to return if class is not allowed
            and raise_error is set to False. This defaults to False.

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
                # TODO: keep an eye on this: I just switched it to return
                # False rather than None by default, since all the edit methods
                # require a boolean return value. I don't know for sure that
                # none of the rest of my code expects it to return None though
                return return_val
            return function(self, object, *args, **kwargs)
        return decorated_func
    return decorator


class BaseManager(object):
    """Base manager class that all others inherit from."""
    def __init__(self, user_prefs, filter_type, name="", suffix="manager"):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            filter_type (FilterType): filter type of manager.
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
        self._filter_type = filter_type

    @property
    def filter_type(self):
        """Get filter type of manager.

        Returns:
            (FilterType): the filter type of the manager. This means slightly
                different things for different managers: for a filter manager,
                it represents the tab that the filter manager is used on, and
                thus it indicates the FilterType of the filter manager's
                combined_filter property. For other managers, this property
                reflects the type of component that it manages, and thus it
                indicates what type of filter the items it manages will
                accept.
        """
        return self._filter_type

    def _get_filter(self, filter_manager):
        """Get filter that this manager can use.

        Args:
            filter_manager (FilterManager): filter manager to get filter from.

        Returns:
            (BaseFilter): combined_filter from filter_manager, quasiconverted
                so that it's usable by the objects that this class manages.
                Note that this method is intended to be used by the component
                manager classes and not by filter manager classes, but is
                defined in the base class for convenience.
        """
        return quasiconvert_filter(
            filter_manager.combined_filter,
            self.filter_type,
        )

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
    
    @require_class(BaseTaskItem, raise_error=True)
    def is_top_level_task(self, item):
        """Check if tree item is a top level task.

        Args:
            item (BaseTaskItem): tree item to check.

        Return:
            (bool): whether or not item is top level task.
        """
        return isinstance(item, Task) and isinstance(item.parent, TaskCategory)

    @require_class(BaseTaskItem, raise_error=True)
    def is_task_category_or_top_level_task(self, item):
        """Check if tree item is a top level task.

        Args:
            item (BaseTaskItem): tree item to check.

        Return:
            (bool): whether or not item is task category or top level task.
        """
        return (self.is_task_category(item) or self.is_top_level_task(item))
    
    @require_class(BaseTaskItem, raise_error=True)
    def is_tracked_task(self, item):
        """Check if tree item is a tracked task.

        Args:
            item (BaseTaskItem): tree item to check.

        Return:
            (bool): whether or not item is a tracked task.
        """
        return (isinstance(item, Task) and item.is_tracked)

    @require_class((Task, TaskCategory), raise_error=True)
    def get_task_category_or_top_level_task(self, item):
        """Get task category or top level task ancestor of item.

        Args:
            item (BaseTaskItem): tree item to use.

        Return:
            (Task or TaskCategory or None): task category or top level task
                of item, if found.
        """
        if self.is_task_category_or_top_level_task(item):
            return item
        if item.parent is None:
            return None
        return self.get_task_category_or_top_level_task(item.parent)

    @require_class(BaseTaskItem, raise_error=True)
    def can_accept_child(self, parent_item, child_item):
        """Check if tree item can accept given item as a child.

        An item can be dropped UNLESS one of the following is true:
        - The item is an ancestor of the new parent
        - The parent has a child that is not the item but has the item's name
        - the item is not in the parent's allowed children.

        Args:
            parent_item (BaseTaskItem): parent item to check.
            child_item (BaseTaskItem): child item to check if can be accepted.

        Return:
            (bool): whether or not parent item can accept child item.
        """
        if child_item.is_ancestor(parent_item):
            return False
        if (parent_item != child_item.parent
                and child_item.name in parent_item._children.keys()):
            return False
        if type(child_item) not in parent_item._allowed_child_types:
            return False
        return True


# TODO: maybe remove this? I think there might be a strong argument for never
# including the filter manager in with the other managers - because the filter
# managers are tied specifically to a tab each and while the other managers
# are each mostly tied to a specific tab, there are annoying special cases,
# eg. there is a different tree on every tab, and hybrid views mean that
# planner and scheduler can appear in each other's tabs and have to use each
# other's filters. So it's less confusing to make each filterer a completely
# distinct entity and just pass them separately to the tabs.
# class BaseManagerWithFilter(BaseManager):
#     """Base manager class for all classes except the filter manager.

#     This allows all other manager classes to use their own filter manager to
#     edit filters for their specific objects.
#     """
#     def __init__(self, user_prefs, filter_manager, name="", suffix="manager"):
#         """Initialize class.

#         Args:
#             user_prefs (ProjectUserPrefs): project user prefs class.
#             calendar (Calendar): calendar object.
#             filter_manager (FilterManager): filter manager class for managing
#                 filters.
#             name (str): manager name.
#             suffix (str): string to append to name.
#         """
#         self._filter_manager = filter_manager
#         super(BaseCalendarManager, self).__init__(
#             user_prefs,
#             name=name,
#             suffix=suffix,
#         )

#     def clear_filter_caches(self):
#         """Clear all filter caches."""
#         self._filter_manager.clear_filter_caches()


class BaseCalendarManager(BaseManager): #BaseManagerWithFilter
    """Base manager for all calendar classes."""
    def __init__(
            self,
            user_prefs,
            calendar,
            filter_type,
            name="",
            suffix="manager"):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            filter_type (FilterType): filter type of manager.
            name (str): manager name.
            suffix (str): string to append to name.
        """
        self._calendar = calendar
        super(BaseCalendarManager, self).__init__(
            user_prefs,
            filter_type,
            name=name,
            suffix=suffix,
            # filter_manager=filter_manager,
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
