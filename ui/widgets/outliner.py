"""Task Outliner Panel."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task, TaskType
from scheduler.api.tree.task_category import TaskCategory
from scheduler.api.tree.task_root import TaskRoot
from scheduler.ui.models.task_category_model import TaskCategoryModel
from scheduler.ui.utils import launch_message_dialog


class Outliner(QtWidgets.QTreeView):
    """Task Outliner panel."""

    MODEL_UPDATED_SIGNAL = QtCore.pyqtSignal()
    CURRENT_CHANGED_SIGNAL = QtCore.pyqtSignal(
        QtCore.QModelIndex,
        QtCore.QModelIndex
    )

    def __init__(self, tree_root, tree_manager, parent=None):
        """Initialise task outliner.

        Args:
            tree_root (BaseTreeItem): tree root item for outliner model.
            tree_manager (TreeManager): tree manager item.
            parent (QtGui.QWidget or None): QWidget parent of widget. 
        """
        super(Outliner, self).__init__(parent)

        self.tree_manager = tree_manager
        self.root = tree_root

        self._model = TaskCategoryModel(self.root, self.tree_manager, self)
        self._model.dataChanged.connect(
            self.update
        )
        self._model.dataChanged.connect(
            self.MODEL_UPDATED_SIGNAL.emit
        )
        self.setModel(self._model)

        self.reset_view(False)
        self.setHeaderHidden(True)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.header().resizeSection(1, 1)
        self.setItemsExpandable(False)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.viewport().setAcceptDrops(True)

        self.allow_key_events = True

        self.selectionModel().currentChanged.connect(
            self.CURRENT_CHANGED_SIGNAL.emit
        )
        self.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems
        )

    # TODO: rename update in all views, as it conflicts with standard qt function
    def update(self):
        """Update view to pick up changes in model."""
        self.reset_view(keep_selection=True)

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

    def reset_view(self, keep_selection=False):
        """Reset view.

        Args:
            keep_selection (bool): if True, save current selection before
                resetting and reselect any items that still exist.
        """
        selected_items = []
        current_item = None
        if keep_selection:
            selected_items = self._get_selected_items()
            current_item = self._get_current_item()

        # TODO: This is just for debugging, remove later
        dodgy_parents = self.root.get_descendants_with_incorrect_parents()
        if dodgy_parents:
            print (dodgy_parents)

        # force update of view by calling expandAll
        # TODO: Maybe when we've renamed the update function this can call the
        # original update method?
        self.expandAll()

        for item in selected_items:
            item_row = item.index()
            if item_row is None:
                continue
            index = self._model.createIndex(
                item_row,
                0,
                item
            )
            if not index.isValid():
                continue
            self.selectionModel().select(
                index,
                self.selectionModel().SelectionFlag.Select
            )
        if current_item:
            item_row = current_item.index()
            if item_row is not None:
                index = self._model.createIndex(
                    item_row,
                    0,
                    current_item
                )
                if index.isValid():
                    self.selectionModel().setCurrentIndex(
                        index,
                        self.selectionModel().SelectionFlag.Current
                    )

    def keyPressEvent(self, event):
        """Reimplement key event to add hotkeys.

        Args:
            event (PySide.QtGui.QKeyEvent): The event.
        """
        if not self.allow_key_events:
            return
        modifiers = event.modifiers()

        if not modifiers:
            # del: remove item
            if event.key() == QtCore.Qt.Key_Delete:
                selected_items = self._get_selected_items()
                if selected_items:
                    continue_deletion = launch_message_dialog(
                        "Delete the following items?",
                        "\n".join([item.name for item in selected_items]),
                        parent=self
                    )
                    if continue_deletion:
                        for item in selected_items:
                            item.parent.remove_child(item.name)
                    # note we reset model rather than update here
                    # as we don't want to keep selection
                    self.reset_view()
                    self.MODEL_UPDATED_SIGNAL.emit()

        elif modifiers == QtCore.Qt.ControlModifier:
            # ctrl+plus: add new task
            if event.key() in (QtCore.Qt.Key_Plus, QtCore.Qt.Key_Equal):
                current_item = self._get_current_item()
                if current_item:
                    if isinstance(current_item, (TaskCategory, TaskRoot)):
                        current_item.create_new_task()
                        self.update()
                        self.MODEL_UPDATED_SIGNAL.emit()
            # ctrl+asterisk: add new subcategory
            elif event.key() in (QtCore.Qt.Key_Asterisk, QtCore.Qt.Key_8):
                current_item = self._get_current_item()
                if (current_item
                        and type(current_item) in [TaskCategory, TaskRoot]):
                    current_item.create_new_subcategory()
                    self.update()
                    self.MODEL_UPDATED_SIGNAL.emit()
            # ctrl+del: force remove item
            elif event.key() == QtCore.Qt.Key_Delete:
                selected_items = self._get_selected_items()
                if selected_items:
                    for item in selected_items:
                        item.parent.remove_child(item.name)
                    # note we reset model rather than update here
                    # as we don't want to keep selection
                    self.reset_view()
                    self.MODEL_UPDATED_SIGNAL.emit()
            # ctrl+r: switch task to routine
            elif event.key() == QtCore.Qt.Key_R:
                current_item = self._get_current_item()
                if current_item and isinstance(current_item, Task):
                    current_item.change_task_type(TaskType.ROUTINE)
                    self.update()
                    self.MODEL_UPDATED_SIGNAL.emit()
            # ctrl+g: switch task to general
            elif event.key() == QtCore.Qt.Key_G:
                current_item = self._get_current_item()
                if current_item and isinstance(current_item, Task):
                    current_item.change_task_type(TaskType.GENERAL)
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
                    if type(current_item) == TaskCategory:
                        current_item.create_new_sibling_category()
                    elif type(current_item) == Task:
                        current_item.create_new_sibling_task()
                    self.update()
                    self.MODEL_UPDATED_SIGNAL.emit()

        super(Outliner, self).keyPressEvent(event)
