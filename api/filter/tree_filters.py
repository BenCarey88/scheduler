"""Tree filters."""

from collections import OrderedDict

from scheduler.api.tree.task import Task
from scheduler.api.tree.task_category import TaskCategory
from ._base_filter import BaseFilter, FilterFactory


class BaseTreeFilter(BaseFilter):
    """Base tree filter."""
    def __init__(self):
        """Initialize."""
        super(BaseTreeFilter, self).__init__()
        self._filter_builder = FilterFactory(BaseTreeFilter)

    def recursive_filter(self, child_item):
        """Check if an item or any of its ancestors are filtered.

        Args:
            child_item (BaseTreeItem):

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


NoFilter = FilterFactory(BaseTreeFilter, no_filter=True)


class FullPrune(BaseTreeFilter):
    """Filter to remove all children."""
    def filter_function(self, child_item):
        return False


class KeepChildrenOfType(BaseTreeFilter):
    """Filter to keep only the items of the given type."""
    def __init__(self, class_type):
        super(KeepChildrenOfType, self).__init__()
        self.class_type = class_type

    def filter_function(self, child_item):
        return isinstance(child_item, self.class_type)


class RemoveChildrenOfType(BaseTreeFilter):
    """Filter to remove all items of the given type."""
    def __init__(self, class_type):
        super(RemoveChildrenOfType, self).__init__()
        self.class_type = class_type

    def filter_function(self, child_item):
        return not isinstance(child_item, self.class_type)


class RemoveSubChildrenOfType(BaseTreeFilter):
    """Filter to remove all children of items with the given type."""
    def __init__(self, class_type):
        super(RemoveSubChildrenOfType, self).__init__()
        self.class_type = class_type

    def filter_function(self, child_item):
        return not isinstance(child_item.parent, self.class_type)


class RemoveGivenChildren(BaseTreeFilter):
    """Filter to remove the given children."""
    def __init__(self, specified_parent, children_to_remove):
        """Initialise filter.

        Args:
            specified_parent (BaseTreeItem): parent to restrict children of.
            children_to_keep (list(str)): names of children to keep for given
                parent.
        """
        super(RemoveGivenChildren, self).__init__()
        self.specified_parent = specified_parent
        self.children_to_remove = children_to_remove

    def filter_function(self, child_item):
        if (child_item.parent == self.specified_parent
                and child_item.name in self.children_to_remove):
            return False
        return True


class RestrictToGivenChildren(BaseTreeFilter):
    """Filter to remove all but the given children for specified parent."""

    def __init__(self, specified_parent, children_to_keep):
        """Initialise filter.

        Args:
            specified_parent (BaseTreeItem): parent to restrict children of.
            children_to_keep (list(str)): names of children to keep for given
                parent.
        """
        super(RestrictToGivenChildren, self).__init__()
        self.specified_parent = specified_parent
        self.children_to_keep = children_to_keep

    def filter_function(self, child_item):
        if (child_item.parent == self.specified_parent
                and child_item.name not in self.children_to_keep):
            return False
        return True


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


class TaskFilter(KeepChildrenOfType):
    """Filter for tasks in child dict."""
    def __init__(self):
        super(TaskFilter, self).__init__(Task)


class TaskCategoryFilter(KeepChildrenOfType):
    """Filter for task categories in child dict."""
    def __init__(self):
        super(TaskCategoryFilter, self).__init__(TaskCategory)


class NoTasks(RemoveChildrenOfType):
    """Filter to remove all tasks from child dicts."""
    def __init__(self):
        super(NoTasks, self).__init__(Task)


class NoSubtasks(RemoveSubChildrenOfType):
    """Filter to remove all subtasks from child dicts."""
    def __init__(self):
        super(NoSubtasks, self).__init__(Task)

