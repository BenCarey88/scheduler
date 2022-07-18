"""Filters for scheduler."""

from scheduler.api.calendar.scheduled_item import ScheduledItemType
from ._base_filter import BaseFilter, FilterFactory


class BaseSchedulerFilter(BaseFilter):
    """Base filter."""
    def __init__(self):
        """Initialize."""
        super(BaseSchedulerFilter, self).__init__()
        self._filter_builder = FilterFactory(BaseSchedulerFilter)


NoFilter = FilterFactory(BaseSchedulerFilter, no_filter=True)


class NoTaskItems(BaseSchedulerFilter):
    """Filter to only include non-task items."""
    def filter_function(self, scheduled_item):
        return scheduled_item.type != ScheduledItemType.TASK


class OnlyTaskEvents(BaseSchedulerFilter):
    """Filter to only include task events."""
    def filter_function(self, scheduled_item):
        return scheduled_item.type == ScheduledItemType.TASK


class TaskTreeFilter(BaseSchedulerFilter):
    """Apply task tree filter to calendar task events."""
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
