"""TaskTab tab."""

from collections import OrderedDict
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.tabs.base_tab import BaseTab
from .task_category_widget import TaskCategoryWidget

class TaskTab(BaseTab):
    """Task Tab main view."""

    def __init__(self, tree_root, parent=None):
        """Setup task main view.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TaskTab, self).__init__(tree_root, parent)
        self.task_widget_tree = OrderedDict()
        self.category_widget_tree = OrderedDict()
        self._active_task_path = None
        self.selected_subtask_item = None
        self._fill_main_view()
        self._fill_scroll_area()

    def update(self):
        """Update view to sync with model.

        This is done by deleting and then recreating the scroll area and
        main view.
        """
        self.task_widget_tree = OrderedDict()
        self.category_widget_tree = OrderedDict()
        self.scroll_area.deleteLater()
        self._fill_main_view()
        self._fill_scroll_area()

    def _fill_main_view(self):
        """Fill main task view from tree root.

        This also sets the size on the view so that the scroll area can use
        it properly.
        """
        self.main_view = QtWidgets.QWidget()
        self.main_view_layout = QtWidgets.QVBoxLayout()
        self.main_view.setLayout(self.main_view_layout)

        minimum_height = 0
        for category in self.tree_root.get_all_children():
            widget = TaskCategoryWidget(
                category,
                tab=self,
                parent=self,
            )
            self.category_widget_tree[category.path] = widget
            self.main_view_layout.addWidget(widget)
            minimum_height += widget.minimumHeight() + 10
        self.main_view.setMinimumSize(
            QtCore.QSize(1000, minimum_height)
        )

    def _fill_scroll_area(self):
        """Create scroll area and set its widget as main view."""
        self.scroll_area = QtWidgets.QScrollArea()
        self.outer_layout.addWidget(self.scroll_area)
        self.scroll_area.setBackgroundRole(QtGui.QPalette.ColorRole.Light)
        self.scroll_area.setWidget(self.main_view)

    def switch_active_task_widget(self, task_item_path, new_index, old_index):
        """Change active task widget to new one.

        This is called whenever an item from a task widget is selected.
        We use it to deselect all items in the old task widget.

        Note that we access the widget by path rather than directly, since
        the widgets are constantly being deleted so saving widgets directly
        as attributes can result in trying to access a deleted widget.

        Args:
            task_item_path (str): path of task whose widget we should set
                as active.
            new_index (QtCore.QModelIndex): index of new task model item.
            old_index (QtCore.QModelIndex): index of old task model item.
        """
        if self._active_task_path:
            active_task_widget = self.task_widget_tree[self._active_task_path]
            active_task_widget.selectionModel().clearSelection()
        self._active_task_path = task_item_path
        selected_subtask_item = new_index.internalPointer()
        if selected_subtask_item:
            self.selected_subtask_item  = selected_subtask_item

    def keyPressEvent(self, event):
        """Reimplement key event to add hotkeys.

        Args:
            event (PySide.QtGui.QKeyEvent): The event.
        """
        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if self._active_task_path:
            if not modifiers:
                if event.key() == QtCore.Qt.Key_Delete:
                    pass
                    # TODO: self._active_task_widget.remove_item()
                if event.key() == QtCore.Qt.Key_Tab:
                    pass
                    # TODO: self._active_task_widget.move_item_down_a_level
                    # would be cool to get drag and drop in outliner too

            elif modifiers == QtCore.Qt.ControlModifier:
                if event.key() == QtCore.Qt.Key_Plus:
                    pass
                    # TODO: self._active_task_widget.add_new_item()

            elif modifiers == QtCore.Qt.ShiftModifier:
                if event.key() == QtCore.Qt.Key_Tab:
                    pass
                    # TODO: self._active_task_widget.move_item_up_a_level

        super(TaskTab, self).keyPressEvent(event)
