"""Filters for items in timetable."""

from .scheduled_item import ScheduledItemType


class BaseFilter(object):
    """Base filter (does nothing)."""
    def filter_function(self, scheduled_items):
        return scheduled_items


class NoTaskItems(BaseFilter):
    """Filter to only non-task items."""
    def filter_function(self, scheduled_items):
        filtered_list = []
        for item in scheduled_items:
            if item.type != ScheduledItemType.Task:
                filtered_list.append(scheduled_items)
        return filtered_list


class OnlyTaskEvents(BaseFilter):
    """Filter to only include task events."""
    def filter_function(self, scheduled_items):
        filtered_list = []
        for event in scheduled_items:
            if event.type == ScheduledItemType.Task:
                filtered_list.append(scheduled_items)
        return filtered_list


class TaskTreeFilter(BaseFilter):
    """Apply task tree filter to timetable task events."""
    def __init__(self, tree_root, tree_filters):
        """Initialise filter.

        Args:
            tree_root (tree.TaskRoot): task root item.
            tree_filters (list(tree.BaseFilter)): 
        """
        self.tree_root = tree_root
        self.tree_filters = tree_filters

    def filter_function(self, scheduled_items):
        """If event is a task that's not in the filtered tree, remove it."""
        filtered_list = []
        for item in scheduled_items:
            if item.type == ScheduledItemType.Task:
                tree_item = item.tree_item
                if not tree_item:
                    continue
                if tree_item.parent:
                    parent = tree_item.parent
                    with parent.filter_children(self.tree_filters):
                        if not parent.get_child(tree_item.name):
                            continue
            filtered_list.append(item)
        return filtered_list
