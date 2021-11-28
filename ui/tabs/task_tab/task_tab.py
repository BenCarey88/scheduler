"""TaskTab tab."""

from collections import OrderedDict
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task
from scheduler.api.tree.task_category import TaskCategory, TaskFilter

from scheduler.ui.tabs.base_tab import BaseTab
from scheduler.ui.utils import simple_message_dialog, suppress_signals
from .task_category_widget import TaskCategoryWidget

class TaskTab(BaseTab):
    """Task Tab main view."""

    def __init__(self, tree_root, tree_manager, outliner, parent=None):
        """Setup task main view.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            tree_manager (TreeManager): tree manager object.
            outliner (Outliner): outliner widget.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TaskTab, self).__init__(
            tree_root,
            tree_manager,
            outliner,
            parent=parent
        )
        self.task_widget_tree = OrderedDict()
        self.category_widget_tree = OrderedDict()
        self._active_task_id = None
        self.selected_subtask_item = None
        self.selected_task_item = None
        self._scroll_value = None
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
        scroll_value = self.scroll_area.verticalScrollBar().value()
        _selected_subtask_item = None
        _active_task_id = None
        if self.selected_subtask_item:
            _selected_subtask_item = self.selected_subtask_item
        if self._active_task_id:
            _active_task_id = self._active_task_id

        self.task_widget_tree = OrderedDict()
        self.category_widget_tree = OrderedDict()
        self.scroll_area.deleteLater()
        self._fill_main_view()
        self._fill_scroll_area(scroll_value)

        if _active_task_id and _selected_subtask_item:
            self._active_task_id = _active_task_id
            self.selected_subtask_item = _selected_subtask_item
            if self.active_task_widget:
                self.active_task_widget.select_subtask_item()
        if self._scroll_value is not None:
            # TODO: fix this bit
            self.scroll_area.verticalScrollBar().setValue(self._scroll_value)

    def _fill_main_view(self):
        """Fill main task view from tree root.

        This also sets the size on the view so that the scroll area can use
        it properly.
        """
        self.main_view = QtWidgets.QWidget()
        self.main_view_layout = QtWidgets.QVBoxLayout()
        self.main_view.setLayout(self.main_view_layout)

        # TODO: add numbers here as constants
        minimum_height = 0
        child_filter = self.tree_manager.child_filter
        child_filters = [child_filter] if child_filter else []
        with self.tree_root.filter_children(child_filters):
            child_list = self.tree_root.get_all_children()
            for i, category in enumerate(child_list):
                if i:
                    self.main_view_layout.addSpacing(40)
                    minimum_height += 40
                widget = TaskCategoryWidget(
                    category,
                    tab=self,
                    parent=self,
                )
                self.category_widget_tree[category.id] = widget
                self.main_view_layout.addWidget(widget)
                minimum_height += widget.minimumHeight() + 10
        self.main_view.setMinimumSize(
            QtCore.QSize(1000, minimum_height)
        )

    def _fill_scroll_area(self, scroll_value=None):
        """Create scroll area and set its widget as main view.

        Args:
            scroll_value (int or None): current position of scroll bar, to
                maintain.
        """
        self.scroll_area = QtWidgets.QScrollArea()
        self.outer_layout.addWidget(self.scroll_area)
        self.scroll_area.setBackgroundRole(QtGui.QPalette.ColorRole.Light)
        self.scroll_area.setWidget(self.main_view)
        if scroll_value:
            self.scroll_area.verticalScrollBar().setValue(scroll_value)

    def switch_active_task_widget(self, task_item_id, new_index, old_index):
        """Change active task widget to new one.

        This is called whenever an item from a task widget is selected.
        We use it to deselect all items in the old task widget.

        Note that we access the widget by path rather than directly, since
        the widgets are constantly being deleted so saving widgets directly
        as attributes can result in trying to access a deleted widget.

        Args:
            task_item_id (str): id of task whose widget we should set active.
            new_index (QtCore.QModelIndex): index of new task model item.
            old_index (QtCore.QModelIndex): index of old task model item.
        """
        if self.active_task_widget:
            self.active_task_widget.selectionModel().clearSelection()
        self._active_task_id = task_item_id
        selected_subtask_item = new_index.internalPointer()
        if selected_subtask_item:
            self.selected_subtask_item  = selected_subtask_item

    @property
    def active_task_widget(self):
        """Get active task widget.

        Returns:
            (TaskWidget or None): active task widget.
        """
        if self._active_task_id:
            return self.task_widget_tree.get(self._active_task_id, None)
        return None

    # TODO: change name to task_header_widget
    @property
    def active_category_widget(self):
        """Get active task category (or top-level task) widget.

        Returns:
            (TaskWidget or None): active task/task category widget.
        """
        if self.selected_task_item:
            return self.category_widget_tree.get(
                self.selected_task_item.id,
                None,
            )
        return None

    def scroll_to_task(self, new_index, old_index):
        """Scroll to the given task or task category.

        Args:
            new_index (QtCore.QModelIndex): index of task or category to
                scroll to.
            old_index (QtCore.QModelIndex): index of old task or category (not
                used, just passed in by the signal that calls this method).
        """
        if not new_index.isValid():
            return
        tree_item = new_index.internalPointer()
        if not tree_item:
            return
        widget = self.category_widget_tree.get(tree_item.id)
        if not widget:
            return
        point = widget.mapTo(self.scroll_area, QtCore.QPoint(0,0))
        # TODO: this doesn't seem to update correctly when application undo is
        # called.
        self.scroll_area.verticalScrollBar().setValue(
            point.y() + self.scroll_area.verticalScrollBar().value()
        )

    # TODO: These are almost all for the current task widget right?
    # so those should probably just be implemented there
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
                    continue_deletion = simple_message_dialog(
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
                elif self.selected_task_item:
                    self.selected_task_item.create_new_subtask()
                    self.update()
                    # Ignore dodgy naming, active cat widget can be a top-level task
                    task_widget = self.active_category_widget
                    if task_widget:
                        task_widget.setFocus(True)
            # ctrl+del: force remove item
            elif event.key() == QtCore.Qt.Key_Delete:
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
