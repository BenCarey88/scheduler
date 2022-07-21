"""Filters for tracked tasks."""

from ._base_filter import BaseFilter, FilterFactory


class BaseTrackerFilter(BaseFilter):
    """Base filter."""
    def __init__(self):
        """Initialize."""
        super(BaseTrackerFilter, self).__init__()
        self._filter_builder = FilterFactory(BaseTrackerFilter)


NoFilter = FilterFactory(BaseTrackerFilter, no_filter=True)


class TaskTreeFilter(BaseTrackerFilter):
    """Apply task tree filter to tracked tasks."""
    def __init__(self, tree_filter):
        """Initialise filter.

        Args:
            tree_filter (BaseTreeFilter): tree filter.
        """
        super(TaskTreeFilter, self).__init__()
        self._tree_filter = tree_filter

    def filter_function(self, task_item):
        """If item is a task that's not in the filtered tree, remove it."""
        return self._tree_filter.recursive_filter(task_item)
