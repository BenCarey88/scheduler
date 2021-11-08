"""TaskTab tab."""

from collections import OrderedDict
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task
from scheduler.api.tree.task_category import TaskCategory, TaskFilter

from scheduler.ui.tabs.base_tab import BaseTab
from scheduler.ui.utils import launch_message_dialog, suppress_signals
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

        self.outliner.CURRENT_CHANGED_SIGNAL.connect(
            self.scroll_to_task
        )

    def update(self):
        """Update view to sync with model.

        This is done by deleting and then recreating the scroll area and
        main view.
        """
        _selected_subtask_item = None
        _active_task_path = None
        if self.selected_subtask_item:
            _selected_subtask_item = self.selected_subtask_item
        if self._active_task_path:
            _active_task_path = self._active_task_path

        self.task_widget_tree = OrderedDict()
        self.category_widget_tree = OrderedDict()
        self.scroll_area.deleteLater()
        self._fill_main_view()
        self._fill_scroll_area()

        if _active_task_path and _selected_subtask_item:
            self._active_task_path = _active_task_path
            self.selected_subtask_item = _selected_subtask_item
            if self.active_task_widget:
                self.active_task_widget.select_subtask_item()

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
        if self.active_task_widget:
            self.active_task_widget.selectionModel().clearSelection()
        self._active_task_path = task_item_path
        selected_subtask_item = new_index.internalPointer()
        if selected_subtask_item:
            self.selected_subtask_item  = selected_subtask_item

    @property
    def active_task_widget(self):
        """Get active task widget.

        Returns:
            (TaskWidget or None): active task widget.
        """
        if self._active_task_path:
            return self.task_widget_tree.get(self._active_task_path, None)
        return None

    def scroll_to_task(self, new_index, old_index):
        """Scroll to the given task or task category.

        Args:
            new_index (QtCore.QModelIndex): index of task or category to
                scroll to.
            old_index (QtCore.QModelIndex): index of old task or category (not
                used, just passed in by the signal that calls this method).
        """
        tree_item = new_index.internalPointer()
        if not tree_item:
            return
        widget = self.category_widget_tree.get(tree_item.path)
        if not widget:
            return
        point = widget.mapTo(self.scroll_area, QtCore.QPoint(0,0))
        self.scroll_area.verticalScrollBar().setValue(
            point.y() + self.scroll_area.verticalScrollBar().value()
        )

    def keyPressEvent(self, event):
        """Reimplement key event to add hotkeys.

        Args:
            event (PySide.QtGui.QKeyEvent): The event.
        """
        modifiers = event.modifiers()

        if not modifiers:
            # del: remove item
            if event.key() == QtCore.Qt.Key_Delete:
                if self.selected_subtask_item:
                    continue_deletion = launch_message_dialog(
                        "Delete {0}?".format(self.selected_subtask_item.name),
                        parent=self
                    )
                    if continue_deletion:
                        self.selected_subtask_item.parent.remove_child(
                            self.selected_subtask_item.name
                        )
                        self.update()

        elif modifiers == QtCore.Qt.ControlModifier:
            # ctrl+plus: add new child
            if event.key() in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
                if self.selected_subtask_item:
                    self.selected_subtask_item.create_new_subtask()
                    self.update()
            # ctrl+del: force remove item
            if event.key() == QtCore.Qt.Key_Delete:
                if self.selected_subtask_item:
                    self.selected_subtask_item.parent.remove_child(
                        self.selected_subtask_item.name
                    )
                    self.update()

        elif modifiers == QtCore.Qt.ShiftModifier:
            if event.key() == QtCore.Qt.Key_Tab:
                pass
                # TODO: self._active_task_widget.move_item_up_a_level

        elif modifiers == (QtCore.Qt.ShiftModifier|QtCore.Qt.ControlModifier):
            # ctrl+shift+plus: add new sibling
            if event.key() in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
                if self.selected_subtask_item:
                    self.selected_subtask_item.create_new_sibling_task()
                    self.update()

        super(TaskTab, self).keyPressEvent(event)
