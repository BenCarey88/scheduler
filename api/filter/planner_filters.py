"""Filters for planner."""

from ._base_filter import (
    BaseFilter,
    CompositeFilter,
    NoFilter,
    register_serializable_filter,
)


class BasePlannerFilter(BaseFilter):
    """Base filter."""
    def __init__(self):
        """Initialize."""
        super(BasePlannerFilter, self).__init__()
        self._composite_filter_class = CompositePlannerFilter


@register_serializable_filter("CompositePlannerFilter")
class CompositePlannerFilter(CompositeFilter, BasePlannerFilter):
    """Composite planner filter class."""


@register_serializable_filter("EmptyPlannerFilter")
class NoFilter(NoFilter, BasePlannerFilter):
    """Empty planner filter."""


class TaskTreeFilter(BasePlannerFilter):
    """Apply task tree filter to planned items."""
    def __init__(self, tree_filter):
        """Initialise filter.

        Args:
            tree_filter (BaseTreeFilter): tree filter.
        """
        super(TaskTreeFilter, self).__init__()
        self._tree_filter = tree_filter

    def _filter_function(self, planned_item):
        """If item is a task that's not in the filtered tree, remove it."""
        if planned_item.tree_item is None:
            return True
        return self._tree_filter.recursive_filter(planned_item.tree_item)
