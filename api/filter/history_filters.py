"""Filters for history dict."""

from ._base_filter import BaseFilter, FilterFactory


class BaseHistoryFilter(BaseFilter):
    """Base filter."""
    def __init__(self):
        """Initialize."""
        super(BaseHistoryFilter, self).__init__()
        self._filter_builder = FilterFactory(BaseHistoryFilter)


NoFilter = FilterFactory(BaseHistoryFilter, no_filter=True)


class TaskTreeFilter(BaseHistoryFilter):
    """Apply task tree filter to history items."""
    def __init__(self, tree_filter):
        """Initialise filter.

        Args:
            tree_filter (BaseTreeFilter): tree filter.
        """
        super(TaskTreeFilter, self).__init__()
        self._tree_filter = tree_filter

    def filter_function(self, task_item, history_dict):
        """If item is a task that's not in the filtered tree, remove it."""
        return self._tree_filter.recursive_filter(task_item)
