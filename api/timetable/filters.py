"""Filters for items in timetable."""

from .calendar_item import CalendarItemType


class BaseFilter(object):
    """Base filter (does nothing)."""
    def filter_function(self, calendar_items):
        return calendar_items


class NoTaskItems(BaseFilter):
    """Filter to only non-task items."""
    def filter_function(self, calendar_items):
        filtered_list = []
        for item in calendar_items:
            if item.type != CalendarItemType.Task:
                filtered_list.append(calendar_items)
        return filtered_list


class OnlyTaskEvents(BaseFilter):
    """Filter to only include task events."""
    def filter_function(self, calendar_items):
        filtered_list = []
        for event in calendar_items:
            if event.type == CalendarItemType.Task:
                filtered_list.append(calendar_items)
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

    def filter_function(self, calendar_items):
        """If event is a task that's not in the filtered tree, remove it."""
        filtered_list = []
        for item in calendar_items:
            if item.type == CalendarItemType.Task:
                with self.tree_root.filter(self.tree_filters):
                    tree_item = item.tree_item
                    if not tree_item:
                        continue
                    if not self.tree_root.get_item_at_path(tree_item.path):
                        continue
            filtered_list.append(item)
        return filtered_list
