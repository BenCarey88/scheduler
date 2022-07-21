"""Filters for planner."""

from ._base_filter import BaseFilter, FilterFactory


class BasePlannerFilter(BaseFilter):
    """Base filter."""
    def __init__(self):
        """Initialize."""
        super(BasePlannerFilter, self).__init__()
        self._filter_builder = FilterFactory(BasePlannerFilter)


NoFilter = FilterFactory(BasePlannerFilter, no_filter=True)


class TaskTreeFilter(BasePlannerFilter):
    """Apply task tree filter to planned items."""
    def __init__(self, tree_filter):
        """Initialise filter.

        Args:
            tree_filter (BaseTreeFilter): tree filter.
        """
        super(TaskTreeFilter, self).__init__()
        self._tree_filter = tree_filter

    def filter_function(self, planned_item):
        """If item is a task that's not in the filtered tree, remove it."""
        if planned_item.tree_item is None:
            return True
        return self._tree_filter.recursive_filter(planned_item.tree_item)
