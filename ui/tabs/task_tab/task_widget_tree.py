"""Class for storing widget and layout data for each tree item."""


class TaskWidgetTree(object):
    """Wrapper around a dict to store data for all task widgets."""
    TASK_HEADER_WIDGET_KEY = "task_header_widget"
    TASK_HEADER_VIEW_KEY = "task_header_view"
    TASK_VIEW_KEY = "task_view"

    def __init__(self):
        """Initialize."""
        self._widget_tree_data = {}

    def add_or_update_item(
            self,
            tree_item,
            task_header_widget=None,
            task_header_view=None,
            task_view=None):
        """Add data for tree item.

        Args:
            tree_item (BaseTaskItem): tree item to add.
            task_header_widget (TaskHeaderWidget or None): the task
                header widget that represents this item, if it's a
                top-level task or category.
            task_header_view (TaskHeaderWidgetView or None): the task
                header widget view used by this item, it's a top-level
                task or category.
            task_view (TaskViewWidget): the task view widget for
                this item, if it's a task.
        """
        data_dict = self._widget_tree_data.setdefault(tree_item, {})
        if task_header_widget is not None:
            data_dict[self.TASK_HEADER_WIDGET_KEY] = task_header_widget
        if task_header_view is not None:
            data_dict[self.TASK_HEADER_VIEW_KEY] = task_header_view
        if task_view is not None:
            data_dict[self.TASK_VIEW_KEY] = task_view

    def remove_item(self, tree_item):
        """Remove tree item from tree.

        Args:
            tree_item (BaseTaskItem): tree item to remove.
        """
        if tree_item in self._widget_tree_data:
            del self._widget_tree_data[tree_item]

    def update_widget_item(self, old_item, new_item):
        """Update widget representing old item to represent new item.

        Args:
            old_item (BaseTaskItem): the tree item the widget used to
                represent.
            new_item (BaseTaskItem): the tree item the widget now represents.
        """
        if new_item in self._widget_tree_data:
            # Can only update if new item isn't already in use.
            return
        old_item_dict = self._widget_tree_data.get(old_item)
        if old_item_dict is not None:
            del self._widget_tree_data[old_item]
            self._widget_tree_data[new_item] = old_item_dict

    def get_task_header_widget(self, tree_item):
        """Get task header widget for item.

        Args:
            tree_item (BaseTaskItem): tree item to query.

        Returns:
            (TaskHeaderWidget or None): task widget for this item, if found.
        """
        return self._widget_tree_data.get(tree_item, {}).get(
            self.TASK_HEADER_WIDGET_KEY
        )

    def get_task_header_view(self, tree_item):
        """Get task header list view widget for item.

        Args:
            tree_item (BaseTaskItem): tree item to query.

        Returns:
            (TaskHeaderListView or None): task list view widget for this item,
                if found.
        """
        return self._widget_tree_data.get(tree_item, {}).get(
            self.TASK_HEADER_VIEW_KEY
        )

    def get_task_view(self, tree_item):
        """Get task header view for item.

        Args:
            tree_item (BaseTaskItem): tree item to query.

        Returns:
            (TaskViewWidget or None): task widget for this item, if found.
        """
        widget = self._widget_tree_data.get(tree_item, {}).get(
            self.TASK_VIEW_KEY
        )
        if widget is None:
            for ancest in tree_item.iter_ancestors(reversed=True, strict=True):
                widget = self.get_task_view(ancest)
                if widget is not None:
                    break
        return widget

