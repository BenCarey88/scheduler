"""TaskTab tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.tabs.base_tab import BaseTab
from scheduler.ui import utils
from .task_header_widget import TaskHeaderWidget, TaskHeaderListView
from .task_widget_layout import TaskWidgetLayout
from .task_widget_tree import TaskWidgetTree


class TaskTab(BaseTab):
    """Task Tab main view."""
    TASK_WIDGET_HEIGHT_BUFFER = 10
    OUTER_CATEGORY_SPACING = 40

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
        self.selected_task_header_item = None
        # self.selected_subtask_item = None
        self._scroll_value = None
        self.task_header_view = TaskHeaderListView(
            self.tree_manager,
            self.tree_root,
            self,
            item_spacing=self.OUTER_CATEGORY_SPACING,
        )
        self.outer_layout.addWidget(self.task_header_view)
        # self._fill_scroll_area()

        self._views_being_reset = []
        tm = self.tree_manager
        tm.register_pre_item_added_callback(self, self.pre_item_added)
        tm.register_item_added_callback(self, self.on_item_added)
        tm.register_pre_item_removed_callback(self, self.pre_item_removed)
        tm.register_item_removed_callback(self, self.on_item_removed)
        tm.register_pre_item_moved_callback(self, self.pre_item_moved)
        tm.register_item_moved_callback(self, self.on_item_moved)
        tm.register_item_modified_callback(self, self.on_item_modified)
        self.task_header_view.apply_filters()

    # def _fill_main_view(self):
    #     """Fill main task view from tree root.

    #     This also sets the size on the view so that the scroll area can use
    #     it properly.
    #     """
    #     self.main_view = QtWidgets.QWidget()
    #     self.main_view_layout = TaskWidgetLayout(
    #         task_widget_tree=self.task_widget_tree,
    #         height_buffer=self.TASK_WIDGET_HEIGHT_BUFFER,
    #         spacing=self.OUTER_CATEGORY_SPACING,
    #     )
    #     self.main_view.setLayout(self.main_view_layout)

    #     for category in self.tree_root.get_all_children():
    #         widget = TaskHeaderWidget(
    #             self.tree_manager,
    #             category,
    #             tab=self,
    #             parent=self,
    #         )
    #         # self.task_header_widget_tree[category] = widget
    #         self.main_view_layout.add_task_header(category, widget)

        # self.main_view.setSizePolicy(
        #     QtWidgets.QSizePolicy.Policy.Ignored,
        #     QtWidgets.QSizePolicy.Policy.Expanding,
        # )
        # self.main_view.setMinimumSize(self.main_view_layout.recommended_size)

    # def _fill_scroll_area(self, scroll_value=None):
    #     """Create scroll area and set its widget as main view.

    #     Args:
    #         scroll_value (int or None): current position of scroll bar, to
    #             maintain.
    #     """
    #     self.scroll_area = QtWidgets.QScrollArea()
    #     self.outer_layout.addWidget(self.scroll_area)
    #     self.scroll_area.setBackgroundRole(QtGui.QPalette.ColorRole.Light)
    #     self.scroll_area.setWidget(self.main_view)
    #     # TODO: TRY TO GET VIEW FILLING WHOLE OF SCROLL AREA
    #     # self.scroll_area.setWidgetResizable(True)
    #     # self.scroll_area.setSizeAdjustPolicy(
    #     #     self.scroll_area.SizeAdjustPolicy.AdjustToContents
    #     # )
    #     if scroll_value is not None:
    #         self.scroll_area.verticalScrollBar().setValue(scroll_value)

    @property
    def active_task_view(self):
        """Get active task view widget.

        Returns:
            (TaskViewWidget or None): active task widget.
        """
        if self._active_task is not None:
            return self.task_widget_tree.get_task_view(self._active_task)
        return None

    @property
    def active_task_header_widget(self):
        """Get active task header widget.

        Returns:
            (TaskHeaderWidget or None): active task header widget.
        """
        if self.selected_task_header_item is not None:
            return self.task_widget_tree.get_task_header_widget(
                self.selected_task_header_item
            )
        return None

    def switch_active_task_view(self, task_item, new_index, old_index):
        """Change active task view to new one.

        This is called whenever an item from a task view widget is selected.
        We use it to deselect all items in the old task widget.

        Note that we access the widget by task item rather than directly, as
        the widgets are constantly being deleted so saving widgets directly
        as attributes can result in trying to access a deleted widget.

        Args:
            task_item (Task): task whose widget we should set active.
            new_index (QtCore.QModelIndex): index of new task model item.
            old_index (QtCore.QModelIndex): index of old task model item.
        """
        if self.active_task_view:
            self.active_task_view.selectionModel().clearSelection()
        self._active_task = task_item
        # selected_subtask_item = new_index.internalPointer()
        # if selected_subtask_item:
        #     self.selected_subtask_item  = selected_subtask_item

    # @property
    # def active_task_header_widget(self):
    #     """Get active task header widget for categories or top-level tasks.

    #     Returns:
    #         (TaskWidget or None): active task/task category widget.
    #     """
    #     if self.selected_task_header_item:
    #         return self.task_header_widget_tree.get(
    #             self.selected_task_header_item,
    #             None,
    #         )
    #     return None

    def pre_item_added(self, item, parent, row):
        """Callback for before an item has been added.

        Args:
            item (BaseTreeItem): the item to be added.
            parent (BaseTreeItem): the parent the item will be added under.
            row (int): the index the item will be added at.
        """
        if self.tree_manager.is_task(parent):
            widget = self.task_widget_tree.get_task_view(parent)
            if widget:
                widget.begin_reset()
                self._views_being_reset = [widget]

    def on_item_added(self, item, parent, row):
        """Callback for after an item has been added.

        Args:
            item (BaseTreeItem): the item that was added.
            parent (BaseTreeItem): the parent the item was added under.
            row (int): the index the item was added at.
        """
        if self._views_being_reset:
            for widget in self._views_being_reset:
                widget.end_reset()
            self._views_being_reset = []
        else:
            task_header_view = self.task_widget_tree.get_task_header_view(
                parent
            )
            if task_header_view:
                task_header_view.insert_header_widget(row, item)
        for anc in item.iter_ancestors(reversed=True):
            list_view = self.task_widget_tree.get_task_header_view(anc)
            if list_view:
                list_view.open_editors()

    def pre_item_removed(self, item, parent, row):
        """Callback for before an item has been removed.

        Args:
            item (BaseTreeItem): the item to be removed.
            parent (BaseTreeItem): the parent of the removed item.
            row (int): the old row of the removed item in its
                parent's child list.
        """
        if not self.tree_manager.is_task_category_or_top_level_task(item):
            widget = self.task_widget_tree.get_task_view(item)
            if widget:
                widget.begin_reset()
                self._views_being_reset = [widget]

    def on_item_removed(self, item, parent, row):
        """Callback for after an item has been removed.

        Args:
            item (BaseTreeItem): the item removed.
            parent (BaseTreeItem): the parent of the removed item.
            row (int): the old index of the removed item in its
                parent's child list.
        """
        if self._views_being_reset:
            for widget in self._views_being_reset:
                widget.end_reset()
            self._views_being_reset = []
        else:
            task_header_view = self.task_widget_tree.get_task_header_view(
                parent
            )
            if task_header_view:
                task_header_view.remove_header_widget(row, item)
        self.task_header_view.update_view()

    def pre_item_moved(self, item, old_parent, old_row, new_parent, new_row):
        """Callback for before an item is moved.

        Args:
            item (BaseTreeItem): the item to be moved.
            old_parent (BaseTreeItem): the original parent of the item.
            old_row (int): the original index of the item.
            new_parent (BaseTreeItem): the new parent of the moved item.
            new_row (int): the new index of the moved item.
        """
        self._views_being_reset = []
        if self.tree_manager.is_task(old_parent):
            old_widget = self.task_widget_tree.get_task_view(old_parent)
            if old_widget:
                old_widget.begin_reset()
                self._views_being_reset.append(old_widget)
        if new_parent != old_parent and self.tree_manager.is_task(new_parent):
            new_widget = self.task_widget_tree.get_task_view(new_parent)
            if new_widget:
                new_widget.begin_reset()
                self._views_being_reset.append(new_widget)

    def on_item_moved(self, item, old_parent, old_row, new_parent, new_row):
        """Callback for after an item has been moved.

        Args:
            item (BaseTreeItem): the item that was moved.
            old_parent (BaseTreeItem): the original parent of the item.
            old_row (int): the original index of the item.
            new_parent (BaseTreeItem): the new parent of the moved item.
            new_row (int): the new index of the moved item.
        """
        if self._views_being_reset:
            for widget in self._views_being_reset:
                widget.end_reset()
            self._views_being_reset = []
            self.task_header_view.update_view()

        if self.tree_manager.is_task_category(old_parent):
            self.on_item_removed(item, old_parent, old_row)
        if self.tree_manager.is_task_category(new_parent):
            self.on_item_added(item, new_parent, new_row)

    def pre_item_modified(self, old_item, new_item):
        """Run callbacks before an item has been modified.

        Args:
            old_item (BaseTreeItem): the item to be modified.
            new_item (BaseTreeItem): the item after modification.
        """
        if not self.tree_manager.is_task_category_or_top_level_task(old_item):
            widget = self.task_widget_tree.get_task_view(old_item)
            if widget:
                widget.begin_reset()
                self._views_being_reset = [widget]

    def on_item_modified(self, old_item, new_item):
        """Run callbacks after an item has been modified.

        Args:
            old_item (BaseTreeItem): the item that was modified.
            new_item (BaseTreeItem): the item after modification.
        """
        if self._views_being_reset:
            for widget in self._views_being_reset:
                widget.end_reset()
            self._views_being_reset = []
        elif self.tree_manager.is_task_category_or_top_level_task(new_item):
            widget = self.task_widget_tree.get_task_header_widget(old_item)
            if widget:
                widget.update_task_item(new_item)
        self.task_header_view.update_view()

    def on_outliner_current_changed(self, tree_item):
        """Callback to scroll to item when current is changed in outliner.

        Args:
            tree_item (BaseTreeItem): new item selected in outliner.
        """
        task_header = self.tree_manager.get_task_category_or_top_level_task(
            tree_item
        )
        widget = self.task_widget_tree.get_task_header_widget(task_header)
        if not widget:
            return
        point = widget.mapTo(self.task_header_view, QtCore.QPoint(0,0))
        self.task_header_view.verticalScrollBar().setValue(
            point.y() + self.task_header_view.verticalScrollBar().value()
        )

    def on_outliner_filter_changed(self, *args):
        """Callback to update view to match current filter."""
        self.task_header_view.apply_filters()

    def keyPressEvent(self, event):
        """Reimplement key event to add hotkeys.

        Args:
            event (PySide.QtGui.QKeyEvent): The event.
        """
        modifiers = event.modifiers()

        if modifiers == QtCore.Qt.ControlModifier:
            # ctrl+plus: add new subtask
            if event.key() in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
                if self.selected_task_header_item:
                    header_widget = self.active_task_header_widget
                    success = self.tree_manager.create_new_subtask(
                        self.selected_task_header_item
                    )
                    if success and header_widget:
                        header_widget.return_focus_to_line_edit()
            # ctrl+asterisk: add new subcategory
            elif event.key() in (QtCore.Qt.Key_Asterisk, QtCore.Qt.Key_8):
                item = self.selected_task_header_item
                if item and self.tree_manager.is_task_category(item):
                    header_widget = self.active_task_header_widget
                    success = self.tree_manager.create_new_subcategory(
                        self.selected_task_header_item
                    )
                    if success and header_widget:
                        header_widget.return_focus_to_line_edit()

        super(TaskTab, self).keyPressEvent(event)
