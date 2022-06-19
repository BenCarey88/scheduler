"""Custom layout class for task widgets."""

from PyQt5 import QtCore, QtGui, QtWidgets


class TaskWidgetTree(object):
    """Wrapper around a dict to store data for all task widgets."""
    LAYOUT_KEY = "layout"
    TASK_HEADER_WIDGET_KEY = "task_widget"
    TASK_VIEW_WIDGET_KEY = "task_view"

    def __init__(self, tab):
        """Initialize."""
        self._widget_tree_data = {}

    def add_or_update_item(
            self,
            tree_item,
            layout,
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
        data_dict[self.LAYOUT_KEY] = layout
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

    def get_layout(self, tree_item):
        """Get layout that tree item lives in.

        Args:
            tree_item (BaseTreeItem): tree item to query.

        Returns:
            (TaskWidgetLayout or None): layout this item lives in, if found.
        """
        return self._widget_tree_data.get(tree_item, {}).get(self.LAYOUT_KEY)

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
            for ancestor in tree_item.iter_ancestors(reversed=True):
                widget = self.get_task_view_widget(ancestor)
                if widget is not None:
                    break
        return widget


class TaskWidgetLayout(QtWidgets.QVBoxLayout):
    """Layout used to store task and task category widgets."""
    SPACING = 40
    RECOMMENDED_WIDTH = 1000

    def __init__(self, task_widget_tree, height_buffer=0, parent=None):
        """Initialize.

        Args:
            task_widget_tree (TaskWidgetTree): widget tree to store data
                for items.
            height_buffer (int): buffer for height calculation. 
            parent (QtWidgets.QWidget or None): parent widget, if exists.
        """
        super(TaskWidgetLayout, self).__init__(parent=parent)
        self._task_widget_tree = task_widget_tree
        self._height_buffer = height_buffer
        self._height = 0

    def add_task_header(self, tree_item, widget, index=None):
        """Add task header widget and some spacing.

        Args:
            tree_item (BaseTreeItem): the tree item we're adding.
            widget (TaskHeaderWidget): widget to add.
            index (int or None): the index of the tree item this corresponds
                to. If given, we add the item in the corresponding space in
                the tree.
        """
        num_widgets = self.count()
        if num_widgets == 0:
            if index is not None and index != 0:
                raise IndexError(
                    "Index {0} is too large for this layout".format(index)
                )
            self.addWidget(widget)
            self._height += widget.minimumHeight() + self._height_buffer

        elif index is None:
            self.addSpacing(self.SPACING)
            self.addWidget(widget)
            self._height += (
                widget.minimumHeight() + self._height_buffer + self.SPACING
            )

        else:
            widget_index = index * 2
            if widget_index < 0 or widget_index > num_widgets:
                raise IndexError(
                    "Index {0} is out of range for this layout".format(index)
                )
            if widget_index == 0:
                self.insertWidget(widget_index, widget)
                self.insertSpacing(widget_index, self.SPACING)
            else:
                self.insertSpacing(widget_index, self.SPACING)
                self.insertWidget(widget_index, widget)
            self._height += (
                widget.minimumHeight() + self._height_buffer + self.SPACING
            )

        self._task_widget_tree.add_or_update_item(
            tree_item,
            layout=self,
            task_header_widget=widget,
        )

    def add_task_view(self, tree_item, widget,):
        """Add task view widget.

        Args:
            tree_item (BaseTreeItem): the tree item we're adding.
            widget (TaskHeaderWidget): widget to add.
        """
        self.addWidget(widget)
        self._task_widget_tree.add_or_update_item(
            tree_item,
            layout=self,
            task_view_widget=widget,
        )
        self._height += widget.minimumHeight()

    def remove_tree_item(self, tree_item):
        """Remove tree item and associated widget and spacing.

        Args:
            tree_item (BaseTreeItem): the tree item we're removing.
        """
        num_widgets = self.count()
        widget = self._task_widget_tree.
        index = self.indexOf(widget)
        if num_widgets == 1:
            spacer = None
        elif index == 0:
            spacer = self.itemAt(index + 1).widget()
        else:
            spacer = self.itemAt(index - 1).widget()

        self.removeWidget(widget)
        widget.deleteLater()
        self._height -= widget.minimumHeight() - self._height_buffer
        if spacer:
            self.removeWidget(spacer)
            spacer.deleteLater()
            self._height -= self.SPACING

        self._task_widget_tree.remove_item(tree_item)

    @property
    def recommended_size(self):
        """Get recommended size for layout.

        Returns:
            (QtCore.QSize): recommended size.
        """
        return QtCore.QSize(self.RECOMMENDED_WIDTH, self._height)
