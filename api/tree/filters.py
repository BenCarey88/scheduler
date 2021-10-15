"""Filters for children in tree models."""


from collections import OrderedDict

from .task import Task
from .task_category import TaskCategory


class BaseFilter(object):
    """Base filter (does nothing)."""
    def filter_function(self, child_dict, item):
        return child_dict


class FullPrune(BaseFilter):
    """Filter to remove all children."""
    def filter_function(self, child_dict, item):
        return OrderedDict()


class RemoveChildrenOfType(BaseFilter):
    """Filter to remove all items of the given type."""

    def __init__(self, class_type):
        self.class_type = class_type

    def filter_function(self, child_dict, item):
        filtered_dict = OrderedDict()
        for key, value in child_dict.items():
            if type(value) != self.class_type:
                filtered_dict[key] = value
        return filtered_dict


class RemoveSubChildrenOfType(BaseFilter):
    """Filter to remove all children of items with the given type."""

    def __init__(self, class_type):
        self.class_type = class_type

    def filter_function(self, child_dict, item):
        if type(item) == self.class_type:
            return OrderedDict()
        return child_dict


class NoTasks(RemoveChildrenOfType):
    """Filter to remove all tasks from child dicts."""
    def __init__(self):
        super(NoTasks, self).__init__(Task)


class NoSubtasks(RemoveSubChildrenOfType):
    """Filter to remove all subtasks from child dicts."""
    def __init__(self):
        super(NoSubtasks, self).__init__(Task)


class RestrictToGivenChildren(BaseFilter):
    """Filter to remove all but the given children for specified parent."""

    def __init__(self, specified_parent, children_to_keep):
        """Initialise filter.

        Args:
            specified_parent (BaseTreeItem): parent to restrict children of.
            children_to_keep (list(str)): names of children to keep for given
                parent.
        """
        self.specified_parent = specified_parent
        self.children_to_keep = children_to_keep

    def filter_function(self, child_dict, item):
        if item != self.specified_parent:
            return child_dict
        filtered_dict = OrderedDict()
        for key, value in child_dict.items():
            if key in self.children_to_keep:
                filtered_dict[key] = value
        return filtered_dict
