"""Class for storing widget and layout data for each tree item."""


class TaskWidgetTree(object):
    """Wrapper around a dict to store data for all task widgets."""
    # LAYOUT_KEY = "layout"
    TASK_HEADER_WIDGET_KEY = "task_widget"
    TASK_VIEW_WIDGET_KEY = "task_view"

    def __init__(self):
        """Initialize."""
        self._widget_tree_data = {}

    def add_or_update_item(
            self,
            tree_item,
            # layout,
            task_header_widget=None,
            task_view_widget=None):
        """Add data for tree item.

        Args:
            tree_item (BaseTreeItem): tree item to add.
            layout (TaskWidgetLayout): layout this item lives in.
            task_header_widget (TaskHeaderWidget or None): the task
                header widget that represents this item, if it's a
                top-level task or category.
            task_view_widget (TaskViewWidget): the task view widget for
                this item, if it's a task.
        """
        data_dict = self._widget_tree_data.setdefault(tree_item, {})
        # data_dict[self.LAYOUT_KEY] = layout
        if task_header_widget is not None:
            data_dict[self.TASK_HEADER_WIDGET_KEY] = task_header_widget
        if task_view_widget is not None:
            data_dict[self.TASK_VIEW_WIDGET_KEY] = task_view_widget

    def remove_item(self, tree_item):
        """Remove tree item from tree.

        Args:
            tree_item (BaseTreeItem): tree item to remove.
        """
        if tree_item in self._widget_tree_data:
            del self._widget_tree_data[tree_item]

    def update_widget_item(self, old_item, new_item):
        """Update widget representing old item to represent new item.

        Args:
            old_item (BaseTreeItem): the tree item the widget used to
                represent.
            new_item (BaseTreeItem): the tree item the widget now represents.
        """
        if new_item in self._widget_tree_data:
            # Can only update if new item isn't already in use.
            return
        old_item_dict = self._widget_tree_data.get(old_item)
        if old_item_dict is not None:
            del self._widget_tree_data[old_item]
            self._widget_tree_data[new_item] = old_item_dict

    # def get_layout(self, tree_item):
    #     """Get layout that tree item lives in.

    #     Args:
    #         tree_item (BaseTreeItem): tree item to query.

    #     Returns:
    #         (TaskWidgetLayout or None): layout this item lives in, if found.
    #     """
    #     return self._widget_tree_data.get(tree_item, {}).get(self.LAYOUT_KEY)

    def get_task_header_widget(self, tree_item):
        """Get task header widget for item.

        Args:
            tree_item (BaseTreeItem): tree item to query.

        Returns:
            (TaskHeaderWidget or None): task widget for this item, if found.
        """
        return self._widget_tree_data.get(tree_item, {}).get(
            self.TASK_HEADER_WIDGET_KEY
        )

    def get_task_view_widget(self, tree_item):
        """Get task header view for item.

        Args:
            tree_item (BaseTreeItem): tree item to query.

        Returns:
            (TaskViewWidget or None): task widget for this item, if found.
        """
        widget = self._widget_tree_data.get(tree_item, {}).get(
            self.TASK_VIEW_WIDGET_KEY
        )
        if widget is None:
            for ancest in tree_item.iter_ancestors(reversed=True, strict=True):
                widget = self.get_task_view_widget(ancest)
                if widget is not None:
                    break
        return widget

    def get_main_task_widget(self, tree_item):
        """Get main task widget for item.

        For task header items, this returns the task header widget. For
        subtasks, this returns the task view widget.

        Args:
            tree_item (BaseTreeItem): tree item to query.

        Returns:
            (TaskViewWidget, TaskHeaderWidget or None): main widget for
                this item, if found.
        """
        widget = self.get_task_header_widget(tree_item)
        if widget is None:
            widget = self.get_task_view_widget(tree_item)
        return widget
