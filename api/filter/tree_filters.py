"""Tree filters."""

from collections import OrderedDict

from ._base_filter import (
    BaseFilter,
    CompositeFilter,
    NoFilter,
    register_serializable_filter,
)
from ._field_filters import FieldFilter


class BaseTreeFilter(BaseFilter):
    """Base tree filter."""
    def __init__(self):
        """Initialize."""
        super(BaseTreeFilter, self).__init__()
        self._composite_filter_class = CompositeTreeFilter

    def recursive_filter(self, child_item):
        """Check if an item or any of its ancestors are filtered.

        Args:
            child_item (BaseTreeItem): item to check.

        Returns:
            (bool): True if item and all ancestors shouldn't be filtered.
        """
        if not self.filter_function(child_item):
            return False
        if child_item.parent is None:
            return True
        return self.recursive_filter(child_item.parent)

    def get_filtered_dict(self, child_dict):
        """Get filtered dict.

        Args:
            child_dict (OrderedDict): child dict to filter.

        Returns:
            (OrderedDict): filtered child dict.
        """
        return OrderedDict([
            (name, child) for name, child in child_dict.items()
            if self.filter_function(child)
        ])


class BaseTreeFieldFilter(FieldFilter, BaseTreeFilter):
    """Tree field filter."""
    def __init__(
            self,
            field_getter,
            field_operator,
            field_value,
            include_matching_descendants=True):
        """Initialize.

        Args:
            field_getter (function): function to get a field value from
                the item we're filtering.
            field_operator (FilterOperator): operator to apply to field.
            field_value (variant): value to use with operator.
            include_matching_descendants (bool): if True, keep an item in
                if any of its descendants are unfiltered.
        """
        super(BaseTreeFieldFilter, self).__init__(
            field_getter,
            field_operator,
            field_value,
        )
        self._include_matching_descendants = include_matching_descendants

    def filter_function(self, item):
        """Check if tree item is filtered.

        Args:
            item (bool): the item to filter.
        """
        filter_func = super(BaseTreeFieldFilter, self).filter_function
        if self._include_matching_descendants:
            return any([
                filter_func(child)
                for child in item.iter_descendants(strict=False)
            ])
        else:
            return filter_func(item)


@register_serializable_filter("CompositeTreeFilter")
class CompositeTreeFilter(CompositeFilter, BaseTreeFilter):
    """Composite tree filter class."""


@register_serializable_filter("EmptyTreeFilter")
class NoFilter(NoFilter, BaseTreeFilter):
    """Empty tree filter."""


class FilterByItem(BaseTreeFilter):
    """Filter to remove given items."""
    def __init__(self, items_to_remove):
        """Initialise filter.

        Args:
            items_to_remove (list(BaseTreeItem)): items to remove.
        """
        super(FilterByItem, self).__init__()
        self._items_to_remove = items_to_remove

    def filter_function(self, child_item):
        if child_item in self._items_to_remove:
            return False
        return True


@register_serializable_filter("TaskStatusFilter")
class TaskStatusFilter(BaseTreeFieldFilter):
    """Filter for given task statuses."""
    def __init__(self, filter_operator, filter_value):
        """Initialize filter.

        Args:
            field_operator (FilterOperator): operator to apply to field.
            field_value (variant): value to use with operator.
        """
        super(TaskStatusFilter, self).__init__(
            lambda task: task.status,
            filter_operator,
            filter_value,
        )


@register_serializable_filter("TaskTypeFilter")
class TaskTypeFilter(BaseTreeFieldFilter):
    """Filter for given task types."""
    def __init__(self, filter_operator, filter_value):
        """Initialize filter.

        Args:
            field_operator (FilterOperator): operator to apply to field.
            field_value (variant): value to use with operator.
        """
        super(TaskTypeFilter, self).__init__(
            lambda task: task.type,
            filter_operator,
            filter_value,
        )


@register_serializable_filter("TaskPathFilter")
class TaskPathFilter(BaseTreeFieldFilter):
    """Filter for given task path strings."""
    def __init__(self, filter_operator, filter_value):
        """Initialize filter.

        Args:
            field_operator (FilterOperator): operator to apply to field.
            field_value (variant): value to use with operator.
        """
        super(TaskPathFilter, self).__init__(
            lambda task: task.path,
            filter_operator,
            filter_value,
        )
