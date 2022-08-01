"""Filters for scheduler."""

from scheduler.api.calendar.scheduled_item import ScheduledItemType
from ._base_filter import (
    BaseFilter,
    CompositeFilter,
    NoFilter,
    register_serializable_filter,
)


class BaseSchedulerFilter(BaseFilter):
    """Base filter."""
    def __init__(self):
        """Initialize."""
        super(BaseSchedulerFilter, self).__init__()
        self._composite_filter_class = CompositeSchedulerFilter


@register_serializable_filter("CompositeSchedulerFilter")
class CompositeSchedulerFilter(CompositeFilter, BaseSchedulerFilter):
    """Composite scheduler filter class."""


@register_serializable_filter("EmptySchedulerFilter")
class NoFilter(NoFilter, BaseSchedulerFilter):
    """Empty scheduler filter."""


class TaskTreeFilter(BaseSchedulerFilter):
    """Apply task tree filter to scheduled task items."""
    def __init__(self, tree_filter):
        """Initialise filter.

        Args:
            tree_filter (BaseTreeFilter): tree filter.
        """
        super(TaskTreeFilter, self).__init__()
        self._tree_filter = tree_filter

    def filter_function(self, scheduled_item):
        """If event is a task that's not in the filtered tree, remove it."""
        if (scheduled_item.tree_item is None
                or scheduled_item.type != ScheduledItemType.TASK):
            return True
        return self._tree_filter.recursive_filter(scheduled_item.tree_item)
