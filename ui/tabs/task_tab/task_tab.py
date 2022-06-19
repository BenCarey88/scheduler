"""TaskTab tab."""

from collections import OrderedDict
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task
from scheduler.api.tree.task_category import TaskCategory, TaskFilter

from scheduler.ui.tabs.base_tab import BaseTab
from scheduler.ui.utils import simple_message_dialog
from .task_header_widget import TaskHeaderWidget
from .task_view_widget import TaskWidget
from .task_widget_layout import TaskWidgetLayout, TaskWidgetTree


class TaskTab(BaseTab):
    """Task Tab main view."""
    TASK_WIDGET_HEIGHT_BUFFER = 10

    def __init__(self, project, parent=None):
        """Setup task main view.

        Args:
            project (Project): the project we're working on.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TaskTab, self).__init__(
            "tasks",
            project,
            parent=parent,
        )
        self.tree_root = project.task_root
        self.task_widget_tree = TaskWidgetTree()
        # self.task_widget_tree = OrderedDict()
        # self.task_header_widget_tree = OrderedDict()
        self._active_task = None
        self.selected_subtask_item = None
        self.selected_task_item = None
        self._scroll_value = None
        self._fill_main_view()
        self._fill_scroll_area()

        tm = self.tree_manager
        tm.register_item_added_callback(self.on_item_added)
        tm.register_item_removed_callback(self.on_item_removed)
        tm.register_item_moved_callback(self.on_item_moved)
        tm.register_item_modified_callback(self.on_item_modified)

    def _fill_main_view(self):
        """Fill main task view from tree root.

        This also sets the size on the view so that the scroll area can use
        it properly.
        """
        self.main_view = QtWidgets.QWidget()
        self.main_view_layout = TaskWidgetLayout(
            task_widget_tree=self.task_widget_tree,
            height_buffer=self.TASK_WIDGET_HEIGHT_BUFFER,
        )
        self.main_view.setLayout(self.main_view_layout)

        child_list = self.tree_manager.get_filtered_children(self.tree_root)
        for category in child_list:
            widget = TaskHeaderWidget(
                self.tree_manager,
                category,
                tab=self,
                parent=self,
            )
            # self.task_header_widget_tree[category] = widget
            self.main_view_layout.add_task_header(category, widget)
        self.main_view.setMinimumSize(self.main_view_layout.recommended_size)

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
        if scroll_value is not None:
            self.scroll_area.verticalScrollBar().setValue(scroll_value)

    # def switch_active_task_widget(self, task_item, new_index, old_index):
    #     """Change active task widget to new one.

    #     This is called whenever an item from a task widget is selected.
    #     We use it to deselect all items in the old task widget.

    #     Note that we access the widget by path rather than directly, since
    #     the widgets are constantly being deleted so saving widgets directly
    #     as attributes can result in trying to access a deleted widget.

    #     Args:
    #         task_item (Task): task whose widget we should set active.
    #         new_index (QtCore.QModelIndex): index of new task model item.
    #         old_index (QtCore.QModelIndex): index of old task model item.
    #     """
    #     if self.active_task_widget:
    #         self.active_task_widget.selectionModel().clearSelection()
    #     self._active_task = task_item
    #     selected_subtask_item = new_index.internalPointer()
    #     if selected_subtask_item:
    #         self.selected_subtask_item  = selected_subtask_item

    # @property
    # def active_task_widget(self):
    #     """Get active task widget.

    #     Returns:
    #         (TaskWidget or None): active task widget.
    #     """
    #     if self._active_task:
    #         return self.task_widget_tree.get(self._active_task, None)
    #     return None

    # @property
    # def active_task_header_widget(self):
    #     """Get active task header widget for categories or top-level tasks.

    #     Returns:
    #         (TaskWidget or None): active task/task category widget.
    #     """
    #     if self.selected_task_item:
    #         return self.task_header_widget_tree.get(
    #             self.selected_task_item,
    #             None,
    #         )
    #     return None

    def on_item_added(self, item, parent, row, update=True):
        """Callback for after an item has been added.

        Args:
            item (BaseTreeItem): the item that was added.
            parent (BaseTreeItem): the parent the item was added under.
            row (int): the index the item was added at.
            update (bool): whether or not to update afterwards.
        """
        if not self.tree_manager.is_task_category_or_top_level_task(item):
            widget = self.get_widget(item)
            widget.reset_view()
        else:
            layout = self.get_layout(parent)
            if self.tree_manager.is_task(item):
                new_widget = TaskWidget()
            else:
                new_widget = TaskHeaderWidget()
            layout.add_task_header(item, new_widget, row)
        if update:
            self.update()

    def on_item_removed(self, item, parent, index, update=True):
        """Callback for after an item has been removed.

        Args:
            item (BaseTreeItem): the item removed.
            parent (BaseTreeItem): the parent of the removed item.
            index (int): the old index of the removed item in its
                parent's child list.
            update (bool): whether or not to update afterwards.
        """
        if not self.tree_manager.is_task_category_or_top_level_task(item):
            widget = self.task_widget_tree.get_task_view_widget(item)
            widget.reset_view()
        else:
            layout = self.task_widget_tree.get_layout(item)
            widget = self.task_widget_tree.get_task_header_widget(item)
            layout.remove_tree_item(item)
        if update:
            self.update()

    def on_item_moved(self, item, old_parent, old_row, new_parent, new_row):
        """Callback for after an item has been moved.

        Args:
            item (BaseTreeItem): the item that was moved.
            old_parent (BaseTreeItem): the original parent of the item.
            old_row (int): the original index of the item.
            new_parent (BaseTreeItem): the new parent of the moved item.
            new_row (int): the new index of the moved item.
        """
        self.on_item_removed(item, old_parent, old_row, update=False)
        self.on_item_added(item, new_parent, new_row)

    def on_item_modified(self, old_item, new_item):
        """Run callbacks after an item has been modified.

        Args:
            old_item (BaseTreeItem): the item that was modified.
            new_item (BaseTreeItem): the item after modification.
        """
        widget = self.get_widget(old_item)
        if not self.tree_manager.is_task_category_or_top_level_task(old_item):
            widget.reset_view()
        else:
            widget.update_fields()
        self.update()

    def on_outliner_current_changed(self, tree_item):
        """Callback to scroll to item when current is changed in outliner.

        Args:
            tree_item (BaseTreeItem): new item selected in outliner.
        """
        category = self.tree_manager.get_task_category_or_top_level_task(
            tree_item
        )
        widget = self.task_header_widget_tree.get(category)
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

        if modifiers == QtCore.Qt.ControlModifier:
            # ctrl+plus: add new child
            if event.key() in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
                if self.selected_task_item:
                    self.tree_manager.create_new_subtask(
                        self.selected_task_item
                    )
                    self.update()
                    # task_widget = self.active_category_widget
                    # if task_widget:
                    #     task_widget.setFocus(True)

        super(TaskTab, self).keyPressEvent(event)
