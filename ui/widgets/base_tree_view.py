"""Base tree view for outliner, task view and item dialogs."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

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
        self._allow_key_events = True

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

    def keyPressEvent(self, event):
        """Reimplement key event to add hotkeys.

        Args:
            event (PySide.QtGui.QKeyEvent): The event.
        """
        if not self._allow_key_events:
            return
        modifiers = event.modifiers()

        if not modifiers:
            # del: remove item
            if event.key() == QtCore.Qt.Key_Delete:
                selected_items = self._get_selected_items()
                if selected_items:
                    continue_deletion = utils.simple_message_dialog(
                        "Delete the following items?",
                        "\n".join([item.name for item in selected_items]),
                        parent=self
                    )
                    if continue_deletion:
                        for item in selected_items:
                            self.tree_manager.remove_child(
                                item.parent,
                                item.name,
                            )
                    # note we reset model rather than update here
                    # as we don't want to keep selection
                    self.reset_view()
                    self.MODEL_UPDATED_SIGNAL.emit()

        elif modifiers == QtCore.Qt.ControlModifier:
            # ctrl+plus: add new task
            if event.key() in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
                current_item = self._get_current_item()
                if current_item is not None:
                    if self.tree_manager.create_new_subtask(current_item):
                        self.update()
                        self.MODEL_UPDATED_SIGNAL.emit()
            # ctrl+asterisk: add new subcategory
            elif event.key() in (QtCore.Qt.Key_Asterisk, QtCore.Qt.Key_8):
                current_item = self._get_current_item()
                if self.tree_manager.create_new_subcategory(current_item):
                    self.update()
                    self.MODEL_UPDATED_SIGNAL.emit()
            # ctrl+up: move task up an index
            elif event.key() == QtCore.Qt.Key_Up:
                current_item = self._get_current_item()
                if current_item:
                    index = current_item.index()
                    if index is not None:
                        self.tree_manager.move_item_local(
                            current_item,
                            index - 1,
                        )
                        self.update()
                        self.MODEL_UPDATED_SIGNAL.emit()
            # ctrl+down: move task down an index
            elif event.key() == QtCore.Qt.Key_Down:
                current_item = self._get_current_item()
                if current_item:
                    index = current_item.index()
                    if index is not None:
                        current_item.move(index + 1)
                        self.update()
                        self.MODEL_UPDATED_SIGNAL.emit()
            # ctrl+del: force remove item
            elif event.key() == QtCore.Qt.Key_Delete:
                selected_items = self._get_selected_items()
                if selected_items:
                    for item in selected_items:
                        self.tree_manager.remove_child(
                            item.parent,
                            item.name,
                        )
                    # note we reset model rather than update here
                    # as we don't want to keep selection
                    self.reset_view()
                    self.MODEL_UPDATED_SIGNAL.emit()
            # ctrl+r: switch task to routine
            elif event.key() == QtCore.Qt.Key_R:
                current_item = self._get_current_item()
                if self.tree_manager.change_task_type(current_item):
                    self.update()
                    self.MODEL_UPDATED_SIGNAL.emit()
            # ctrl+h: hide or unhide filtered items in outliner
            elif event.key() == QtCore.Qt.Key_H:
                self._hide_filtered_items = not self._hide_filtered_items
                self.update()
                self.MODEL_UPDATED_SIGNAL.emit()
            # ctrl+e: auto-collapse and expand based on filter-status
            elif event.key() == QtCore.Qt.Key_E:
                self.tree_manager.set_expanded_from_filtered(self.root)
                self.update()
                self.MODEL_UPDATED_SIGNAL.emit()

        elif modifiers == QtCore.Qt.ShiftModifier:
            if event.key() == QtCore.Qt.Key_Tab:
                pass
                # TODO: self._active_task_widget.move_item_up_a_level

        elif modifiers == (QtCore.Qt.ShiftModifier|QtCore.Qt.ControlModifier):
            # ctrl+shift+plus: add new sibling
            if event.key() in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
                current_item = self._get_current_item()
                if current_item:
                    if self.tree_manager.create_new_sibling(current_item):
                        self.update()
                        self.MODEL_UPDATED_SIGNAL.emit()

        super(BaseTreeView, self).keyPressEvent(event)

    def _build_right_click_menu(self, item=None):
        """Build right click menu for given item.

        Args:
            item (BaseTreeItem or None): item to build menu for.

        Returns:
            (QtWidgets.QMenu): the right click menu.
        """
        right_click_menu =  QtWidgets.QMenu("Right Click Menu")
        action = right_click_menu.addAction("Save")
        action.triggered.connect(partial(self.test, item))
        return right_click_menu

    def mousePressEvent(self, event):
        """Reimplement mouse press event to add right click menu.

        Args:
            event (PySide.QtGui.QKeyEvent): The event.
        """
        if event.button() == QtCore.Qt.MouseButton.RightButton:
            index = self.indexAt(event.pos())
            item = index.internalPointer() if index.isValid() else None
            right_click_menu = self._build_right_click_menu(item)
            right_click_menu.exec(self.mapToGlobal(event.pos()))
        super(BaseTreeView, self).mousePressEvent(event)

    def test(self, item):
        if item is not None:
            print (item.path)
        else:
            print (None)
