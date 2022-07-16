"""Base tree view for outliner, task view and item dialogs."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.edit.edit_callbacks import CallbackType
from scheduler.api.tree import TaskType

from scheduler.ui import utils


class BaseTreeView(QtWidgets.QTreeView):
    """Base tree view for outliner, task view and item dialogs."""

    def __init__(self, tree_manager, parent=None):
        """Initialise base tree view.

        Args:
            tree_manager (TreeManager): tree manager item.
            parent (QtGui.QWidget or None): QWidget parent of widget. 
        """
        super(BaseTreeView, self).__init__(parent)
        self.tree_manager = tree_manager
        self.root = tree_manager.tree_root

        self._allow_right_click_menu = True
        self._allow_key_events = True
        self._is_full_tree = False
        self._only_delete_current_item = False

        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.viewport().setAcceptDrops(True)

    def pre_edit_callback(self, callback_type, *args):
        """Callback for before an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        if callback_type == CallbackType.TREE_ADD:
            self.model().pre_item_added(*args)
        elif callback_type == CallbackType.TREE_REMOVE:
            self.model().pre_item_removed(*args)
        elif callback_type == CallbackType.TREE_MOVE:
            self.model().pre_item_moved(*args)

    def post_edit_callback(self, callback_type, *args):
        """Callback for after an edit of any type is run.

        Args:
            callback_type (CallbackType): edit callback type.
            *args: additional args dependent on type of edit.
        """
        if callback_type == CallbackType.TREE_ADD:
            self.model().on_item_added(*args)
        elif callback_type == CallbackType.TREE_REMOVE:
            self.model().on_item_removed(*args)
        elif callback_type == CallbackType.TREE_MOVE:
            self.model().on_item_moved(*args)
        elif callback_type == CallbackType.TREE_MODIFY:
            self.model().on_item_modified(*args)

    def _get_selected_items(self):
        """Get tree items that are selected.

        Returns:
            (list(BaseTreeItem)): selected tree items.
        """
        return [
            index.internalPointer()
            for index in self.selectedIndexes()
            if index.isValid()
        ]

    def _get_current_item(self):
        """Get current tree item.

        Returns:
            (BaseTreeItem or None): current tree item, if there is one.
        """
        return (
            self.currentIndex().internalPointer()
            if self.currentIndex().isValid()
            else None
        )

    def remove_items(self, items, force=False, *args):
        """Remove items.

        Args:
            items (list(BaseTreeItem) or None): items to remove.
            force (bool): if False, show user dialog to prompt continuation.

        Returns:
            (bool): whether or not action was successful.
        """
        if not items:
            return False
        if not force:
            # TODO: fix this message (after sorting archiving)
            # - should be in separate function
            # - deal with planned/scheduled children
            messages = []
            dependencies = {}
            for item in items:
                item_dependencies = {
                    "planned": [
                        *(item.planned_year_items),
                        *(item.planned_month_items),
                        *(item.planned_day_items),
                        *(item.planned_week_items),
                    ],
                    "scheduled": [
                        *(item.scheduled_items),
                        *(item.repeat_scheduled_items),
                    ]
                }
                item_dependencies = {
                    k:v for k,v in item_dependencies.items() if v
                }
                if item_dependencies:
                    dependencies[item] = item_dependencies
            for item, deps in dependencies.items():
                messages.append(
                    "WARNING: {0} is planned for the following time periods:\n\t"
                    "{1}\nand scheduled for the following datetimes:\n\t{2}"
                    "".format(
                        item.name,
                        "\n\t".join([
                            planned_item.calendar_period.full_name
                            for planned_item in deps.get("planned", [])
                        ]),
                        "\n\t".join([
                            scheduled_item.date.string()
                            for scheduled_item in deps.get("scheduled", [])
                        ]),
                    )
                )
            continue_deletion = utils.simple_message_dialog(
                "Delete the following items?",
                (
                    "\n".join([item.name for item in items])
                    + "\n\n" + "\n".join(messages)
                ),
                parent=self
            )
            if not continue_deletion:
                return False
        success = False
        for item in items:
            # TODO: stack these edits, or make them a single edit
            success = self.tree_manager.remove_item(item) or success
        return success

    def add_subtask(self, item, *args):
        """Add task child to item.

        Args:
            item (BaseTreeItem or None): item to add to.

        Returns:
            (bool): whether or not action was successful.
        """
        if item is None:
            return False
        index = self.model().get_index_from_item(item)
        if index:
            self.expand(index)
        return self.tree_manager.create_new_subtask(item)

    def add_subcategory(self, item, *args):
        """Add category child to item.

        Args:
            item (BaseTreeItem or None): item to add to.

        Returns:
            (bool): whether or not action was successful.
        """
        if item is None:
            return False
        index = self.model().get_index_from_item(item)
        if index:
            self.expand(index)
        return self.tree_manager.create_new_subcategory(item)

    def add_sibling_item(self, item, *args):
        """Add sibling for given item.

        Args:
            item (BaseTreeItem or None): item to add sibling to.

        Returns:
            (bool): whether or not action was successful.
        """
        if item is None:
            return False
        return self.tree_manager.create_new_sibling(item)

    def move_item_one_space(self, item, up=False, *args):
        """Move item one space up or down in sibling list.

        Args:
            item (BaseTreeItem or None): item to move.
            up (bool): if True, move up, else move down a space.

        Returns:
            (bool): whether or not action was successful.
        """
        if item is None:
            return False
        row = item.index()
        if row is None:
            return False
        new_row = row - 1 if up else row + 1
        return self.tree_manager.move_item_local(item, new_row)

    def toggle_task_type(self, item, *args):
        """Switch task to routine or back again.

        Args:
            item (BaseTreeItem or None): item to switch.

        Returns:
            (bool): whether or not action was successful.
        """
        if item is None:
            return False
        return self.tree_manager.change_task_type(item)

    def keyPressEvent(self, event):
        """Reimplement key event to add hotkeys.

        Args:
            event (PySide.QtGui.QKeyEvent): The event.
        """
        if not self._allow_key_events:
            return
        modifiers = event.modifiers()
        selected_items = self._get_selected_items()
        current_item = self._get_current_item()

        success = False
        if not modifiers:
            # del: remove item
            if event.key() == QtCore.Qt.Key_Delete:
                items = (
                    [current_item] if self._only_delete_current_item
                    else selected_items
                )
                success = self.remove_items(items, force=False)

        elif modifiers == QtCore.Qt.ControlModifier:
            # ctrl+plus: add new task
            if event.key() in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
                success = self.add_subtask(current_item)
            # ctrl+asterisk: add new subcategory
            elif event.key() in (QtCore.Qt.Key_Asterisk, QtCore.Qt.Key_8):
                success = self.add_subcategory(current_item)
            # ctrl+up: move task up an index
            elif event.key() == QtCore.Qt.Key_Up:
                success = self.move_item_one_space(current_item, up=True)
            # ctrl+down: move task down an index
            elif event.key() == QtCore.Qt.Key_Down:
                success = self.move_item_one_space(current_item, up=False)
            # ctrl+del: force remove item
            elif event.key() == QtCore.Qt.Key_Delete:
                items = (
                    [current_item] if self._only_delete_current_item
                    else selected_items
                )
                success = self.remove_items(items, force=True)
            # ctrl+r: switch task to routine
            elif event.key() == QtCore.Qt.Key_R:
                success = self.toggle_task_type(current_item)
            # ctrl+tab: move item down a level
            elif event.key() == QtCore.Qt.Key_Tab:
                pass
                # self.move_item_up_or_down_a_level(self, item, up=False)

        elif modifiers == QtCore.Qt.ShiftModifier:
            # shift+tab: move item up a level
            if event.key() == QtCore.Qt.Key_Tab:
                pass
                #self.move_item_up_or_down_a_level(self, item, up=True)

        elif modifiers == (QtCore.Qt.ShiftModifier|QtCore.Qt.ControlModifier):
            # ctrl+shift+plus: add new sibling
            if event.key() in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
                success = self.add_sibling_item(current_item)

        if success:
            # ensure focus remains on this widget after callbacks
            self.setFocus(True)
        else:
            super(BaseTreeView, self).keyPressEvent(event)

    def _connect_action_to_func(self, action, func, *args, **kwargs):
        """Connect action to given function and then update view.

        Args:
            action (QtCore.QAction): action to connect.
            func (function): function to connect to.
            args (list): args to pass to func.
            kwargs (dict): kwargs to pass to func.
        """
        def decorated_func(triggered):
            func(*args, **kwargs)
        action.triggered.connect(decorated_func)

    def _build_right_click_menu(self, item=None):
        """Build right click menu for given item.

        Args:
            item (BaseTreeItem or None): item to build menu for.

        Returns:
            (QtWidgets.QMenu): the right click menu.
        """
        right_click_menu = QtWidgets.QMenu("Right Click Menu")

        if self._is_full_tree:
            action = right_click_menu.addAction("Create root category")
            self._connect_action_to_func(
                action,
                partial(self.add_subcategory, item=self.root)
            )

        if item is not None:
            right_click_menu.addSeparator()
            if self.tree_manager.is_task_category(item):
                action = right_click_menu.addAction("Add subcategory")
                self._connect_action_to_func(
                    action,
                    partial(self.add_subcategory, item=item)
                )

            action = right_click_menu.addAction("Add subtask")
            self._connect_action_to_func(
                action,
                partial(self.add_subtask, item=item)
            )

            action = right_click_menu.addAction("Add sibling")
            self._connect_action_to_func(
                action,
                partial(self.add_sibling_item, item=item)
            )

            if self.tree_manager.is_task(item):
                if item.type == TaskType.ROUTINE:
                    action = right_click_menu.addAction("Make non-routine")
                else:
                    action = right_click_menu.addAction("Make routine")
                    self._connect_action_to_func(
                        action,
                        partial(self.toggle_task_type, item=item)
                    )

            action = right_click_menu.addAction("Delete")
            self._connect_action_to_func(
                action,
                partial(self.remove_items, items=[item], force=True)
            )

        return right_click_menu

    def mousePressEvent(self, event):
        """Reimplement mouse press event to add right click menu.

        Args:
            event (PySide.QtGui.QKeyEvent): The event.
        """
        if self._allow_right_click_menu:
            if event.button() == QtCore.Qt.MouseButton.RightButton:
                index = self.indexAt(event.pos())
                item = index.internalPointer() if index.isValid() else None
                right_click_menu = self._build_right_click_menu(item)
                right_click_menu.exec(self.mapToGlobal(event.pos()))
        super(BaseTreeView, self).mousePressEvent(event)
