"""Custom layout class for task widgets."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.utils import fallback_value


class TaskWidgetLayout(QtWidgets.QVBoxLayout):
    """Layout used to store task and task category widgets."""
    DEFAULT_SPACING = 10
    RECOMMENDED_WIDTH = 1000

    def __init__(self, task_widget_tree, height_buffer=0, spacing=None):
        """Initialize.

        Args:
            task_widget_tree (TaskWidgetTree): widget tree to store data
                for items.
            height_buffer (int): buffer for height calculation.
            spacing (int or None): spacing between items. If None, we use
                default spacing.
        """
        super(TaskWidgetLayout, self).__init__()
        self._task_widget_tree = task_widget_tree
        self._height_buffer = height_buffer
        self._height = 0
        self._spacing = fallback_value(spacing, self.DEFAULT_SPACING)
        self.setSpacing(self._spacing)
        self.setSizeConstraint(self.SizeConstraint.SetFixedSize)

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
            # self._height += widget.minimumHeight() + self._height_buffer

        elif index is None:
            self.addWidget(widget)
            # self._height += (
            #     widget.minimumHeight() + self._height_buffer + self._spacing
            # )

        else:
            if index < 0 or index > num_widgets:
                raise IndexError(
                    "Index {0} is out of range for this layout".format(index)
                )
            if index == num_widgets:
                self.addWidget(widget)
            else:
                self.insertWidget(index, widget)
            # self._height += (
            #     widget.minimumHeight() + self._height_buffer + self._spacing
            # )

        self._task_widget_tree.add_or_update_item(
            tree_item,
            layout=self,
            task_header_widget=widget,
        )

    def add_task_view(self, tree_item, widget):
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
        # self._height += widget.minimumHeight()

    def remove_tree_item(self, tree_item):
        """Remove tree item and associated widget and spacing.

        Args:
            tree_item (BaseTreeItem): the tree item we're removing.
        """
        widget = self._task_widget_tree.get_main_task_widget(tree_item)
        index = self.indexOf(widget)
        if index == -1:
            return

        self.removeWidget(widget)
        widget.deleteLater()
        self._height -= widget.minimumHeight() - self._height_buffer

        self._task_widget_tree.remove_item(tree_item)

    @property
    def recommended_size(self):
        """Get recommended size for layout.

        Returns:
            (QtCore.QSize): recommended size.
        """
        return QtCore.QSize(self.RECOMMENDED_WIDTH, self._height)
