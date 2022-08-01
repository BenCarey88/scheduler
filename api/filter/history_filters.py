"""Filters for history dict."""

from ._base_filter import (
    BaseFilter,
    CompositeFilter,
    NoFilter,
    register_serializable_filter,
)


class BaseHistoryFilter(BaseFilter):
    """Base filter."""
    def __init__(self):
        """Initialize."""
        super(BaseHistoryFilter, self).__init__()
        self._composite_filter_class = CompositeHistoryFilter


@register_serializable_filter("CompositeHistoryFilter")
class CompositeHistoryFilter(CompositeFilter, BaseHistoryFilter):
    """Composite history filter class."""


@register_serializable_filter("EmptyHistoryFilter")
class NoFilter(NoFilter, BaseHistoryFilter):
    """Empty history filter."""


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
