"""Base tree view for outliner, task view and item dialogs."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree import TaskType

from scheduler.ui import utils


class BaseTreeView(QtWidgets.QTreeView):
    """Base tree view for outliner, task view and item dialogs."""

    def __init__(self, tab, tree_manager, parent=None):
        """Initialise base tree view.

        Args:
            tab (BaseTab): tab that this tree view is being used in.
            tree_manager (TreeManager): tree manager item.
            parent (QtGui.QWidget or None): QWidget parent of widget. 
        """
        super(BaseTreeView, self).__init__(parent)
        self.tab = tab
        self.tree_manager = tree_manager
        self.root = tree_manager.tree_root

        self._allow_right_click_menu = True
        self._allow_key_events = True
        self._is_full_tree = False
        self._is_outliner = False
        self._only_delete_current_item = False

    class _Decorators(object):
        """Internal decorators class."""
        @staticmethod
        def action_decorator(method):
            """Decorator for user action functions.

            Args:
                method (function): the method to decorate.

            Returns:
                (function): the decorated method. This runs the method and
                    then calls update after.
            """
            def decorated_func(self, *args, **kwargs):
                method(self, *args, **kwargs)
                self.update()
                self.MODEL_UPDATED_SIGNAL.emit()
            return decorated_func

        @staticmethod
        def item_action_decorator(method):
            """Decorator for user action functions.

            Args:
                method (function): the method to decorate.

            Returns:
                (function): the decorated method. This runs the method and
                    then calls update after. It also first checks if the
                    first argument is None and returns if so.
            """
            def decorated_func(self, item, *args, **kwargs):
                if not item:
                    return
                if method(self, item, *args, **kwargs):
                    self.update()
                    self.MODEL_UPDATED_SIGNAL.emit()
            return decorated_func

    _action_decorator = _Decorators.action_decorator
    _item_action_decorator = _Decorators.item_action_decorator

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

    @_item_action_decorator
    def remove_items(self, items, force=False, *args):
        """Remove items.

        Args:
            items (list(BaseTreeItem) or None): items to remove.
            force (bool): if False, show user dialog to prompt continuation.

        Returns:
            (bool): whether or not action was successful.
        """
        if not force:
            continue_deletion = utils.simple_message_dialog(
                "Delete the following items?",
                "\n".join([item.name for item in items]),
                parent=self
            )
            if not continue_deletion:
                return False
        success = False
        for item in items:
            # TODO: this should not be separate edits.
            success = self.tree_manager.remove_child(
                item.parent,
                item.name,
            ) or success
        return success

    @_item_action_decorator
    def add_subtask(self, item, *args):
        """Add task child to item.

        Args:
            item (BaseTreeItem or None): item to add to.

        Returns:
            (bool): whether or not action was successful.
        """
        return self.tree_manager.create_new_subtask(item)

    @_item_action_decorator
    def add_subcategory(self, item, *args):
        """Add category child to item.

        Args:
            item (BaseTreeItem or None): item to add to.

        Returns:
            (bool): whether or not action was successful.
        """
        return self.tree_manager.create_new_subcategory(item)

    @_item_action_decorator
    def move_item_one_space(self, item, up=False, *args):
        """Move item one space up or down in sibling list.

        Args:
            item (BaseTreeItem or None): item to move.
            up (bool): if True, move up, else move down a space.

        Returns:
            (bool): whether or not action was successful.
        """
        index = item.index()
        if index is None:
            return
        new_index = index - 1 if up else index + 1
        return self.tree_manager.move_item_local(item, new_index)

    @_item_action_decorator
    def toggle_task_type(self, item, *args):
        """Switch task to routine or back again.

        Args:
            item (BaseTreeItem or None): item to switch.

        Returns:
            (bool): whether or not action was successful.
        """
        return self.tree_manager.change_task_type(item)

    # @_item_action_decorator
    # def move_item_up_or_down_a_level(self, item, up=False):
    #     """Move item one level up or down.

    #     Args:
    #         item (BaseTreeItem or None): item to move.
    #         up (bool): if True, move up, else move down a level.
    #     """
    #     pass

    # TODO: down the line these should ideally all be done in the
    # model - that way we can call the relevant rowsAboutToBeInserted
    # functions etc. and not have to reset the model every time (and
    # therefore be forced to deal with expanding and contracting)
    @_item_action_decorator
    def add_sibling_item(self, item, *args):
        """Add sibling for given item.

        Args:
            item (BaseTreeItem or None): item to add sibling to.
        """
        return self.tree_manager.create_new_sibling(item)

    @_action_decorator
    def toggle_items_hidden(self, *args):
        """Hide or unhide filtered items in outliner."""
        self._hide_filtered_items = not self._hide_filtered_items

    @_action_decorator
    def expand_from_filtered(self, *args):
        """Auto expand/collapse items based on which ones are filtered."""
        self.tree_manager.set_expanded_from_filtered(self.root)

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

        if not modifiers:
            # del: remove item
            if event.key() == QtCore.Qt.Key_Delete:
                if self._only_delete_current_item:
                    self.remove_items([current_item], force=False)
                else:
                    self.remove_items(selected_items, force=False)

        elif modifiers == QtCore.Qt.ControlModifier:
            # ctrl+plus: add new task
            if event.key() in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
                self.add_subtask(current_item)
            # ctrl+asterisk: add new subcategory
            elif event.key() in (QtCore.Qt.Key_Asterisk, QtCore.Qt.Key_8):
                self.add_subcategory(current_item)
            # ctrl+up: move task up an index
            elif event.key() == QtCore.Qt.Key_Up:
                self.move_item_one_space(current_item, up=True)
            # ctrl+down: move task down an index
            elif event.key() == QtCore.Qt.Key_Down:
                self.move_item_one_space(current_item, up=False)
            # ctrl+del: force remove item
            elif event.key() == QtCore.Qt.Key_Delete:
                if self._only_delete_current_item:
                    self.remove_items([current_item], force=True)
                else:
                    self.remove_items(selected_items, force=True)
            # ctrl+r: switch task to routine
            elif event.key() == QtCore.Qt.Key_R:
                self.toggle_task_type(current_item)
            # ctrl+tab: move item down a level
            elif event.key() == QtCore.Qt.Key_Tab:
                    pass
                # self.move_item_up_or_down_a_level(self, item, up=False)
            elif self._is_outliner:
                # ctrl+h: hide or unhide filtered items in outliner
                if event.key() == QtCore.Qt.Key_H:
                    self.toggle_items_hidden()
                # ctrl+e: auto-collapse and expand based on filter-status
                elif event.key() == QtCore.Qt.Key_E:
                    self.expand_from_filtered()

        elif modifiers == QtCore.Qt.ShiftModifier:
            # shift+tab: move item up a level
            if event.key() == QtCore.Qt.Key_Tab:
                pass
                # self.move_item_up_or_down_a_level(self, item, up=True)

        elif modifiers == (QtCore.Qt.ShiftModifier|QtCore.Qt.ControlModifier):
            # ctrl+shift+plus: add new sibling
            if event.key() in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
                self.add_sibling_item(current_item)

        super(BaseTreeView, self).keyPressEvent(event)

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
            action.triggered.connect(
                partial(self.add_subcategory, self.root)
            )
        right_click_menu.addSeparator()

        if item is not None:
            if self.tree_manager.is_task_category(item):
                action = right_click_menu.addAction("Add subcategory")
                action.triggered.connect(
                    partial(self.add_subcategory, item)
                )

            action = right_click_menu.addAction("Add subtask")
            action.triggered.connect(
                partial(self.add_subtask, item=item)
            )

            action = right_click_menu.addAction("Add sibling")
            action.triggered.connect(
                partial(self.add_sibling_item, item)
            )

            if self.tree_manager.is_task(item):
                if item.type == TaskType.ROUTINE:
                    action = right_click_menu.addAction("Make non-routine")
                else:
                    action = right_click_menu.addAction("Make routine")
                action.triggered.connect(
                    partial(self.add_subcategory, item)
                )

            action = right_click_menu.addAction("Delete")
            action.triggered.connect(
                partial(self.remove_items, [item], True)
            )
            right_click_menu.addSeparator()

        if self._is_outliner:
            if self._hide_filtered_items:
                action = right_click_menu.addAction("Unhide filtered items")
            else:
                action = right_click_menu.addAction("Hide filtered items")
            action.triggered.connect(self.toggle_items_hidden)

            action = right_click_menu.addAction("Expand from filtered")
            action.triggered.connect(self.expand_from_filtered)

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
