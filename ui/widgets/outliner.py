"""Task Outliner Panel."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task, TaskType
from scheduler.api.tree.task_category import TaskCategory
from scheduler.api.tree.task_root import TaskRoot
from scheduler.ui.models.task_category_model import TaskCategoryModel
from scheduler.ui.utils import simple_message_dialog


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
        self._allow_key_events = True
        self._hide_filtered_items = False

        self.reset_view(False)
        self.setHeaderHidden(True)
        self.header().setStretchLastSection(False)
        self.header().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        self.header().resizeSection(1, 1)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.viewport().setAcceptDrops(True)

        self.expanded.connect(partial(self.mark_item_expanded, value=True))
        self.collapsed.connect(partial(self.mark_item_expanded, value=False))

        # self.setSelectionBehavior(
        #     QtWidgets.QAbstractItemView.SelectionBehavior.SelectItems
        # )

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

    def _expand_item(self, index):
        """Recursively expand item at given index.

        This only expands items marked as expanded in the tree_manager.

        Args:
            index (QtCore.QModelIndex): index of item to expand.
        """
        if not index.isValid():
            return
        item = index.internalPointer()
        if not isinstance(item, TaskCategory):
            return
        if self.tree_manager.is_expanded(item):
            self.setExpanded(index, True)
        else:
            self.setExpanded(index, False)
        for i in range(item.num_children()):
            child_index = self._model.index(i, 0, index)
            self._expand_item(child_index)

    def expand_items(self):
        """Expand all items marked as expanded in tree_manager."""
        for i in range(self.root.num_children()):
            child_index = self._model.index(i, 0, QtCore.QModelIndex())
            self._expand_item(child_index)

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

        # TODO: afaik this is currently only needed for adding siblings to
        # top-level category - I think we should be able to avoid resetting
        # the model every time, so should try to remove this in future.
        # BUT will need to add in an update filters function.
        self._model = TaskCategoryModel(
            self.root,
            self.tree_manager,
            hide_filtered_items=self._hide_filtered_items,
            parent=self
        )
        self._model.dataChanged.connect(
            self.update
        )
        self._model.dataChanged.connect(
            self.MODEL_UPDATED_SIGNAL.emit
        )
        self.setModel(self._model)
        self.selectionModel().currentChanged.connect(
            self.CURRENT_CHANGED_SIGNAL.emit
        )
        # force update of view by calling expandAll
        # TODO: Maybe when we've renamed the update function this can call the
        # original update method?
        self.expand_items()

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

    def mark_item_expanded(self, index, value):
        """Mark item as expanded in tree manager.
        
        This is called whenever an item is collapsed/expanded in the view.

        Args:
            index (QtCore.QModelIndex): index of item.
            value (bool): whether or not the item should be expanded.
        """
        if index.isValid():
            item = index.internalPointer()
            if item:
                self.tree_manager.expand_item(item, value)

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
                    continue_deletion = simple_message_dialog(
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
            # ctrl+up: move task up an index
            elif event.key() == QtCore.Qt.Key_Up:
                current_item = self._get_current_item()
                if current_item:
                    index = current_item.index()
                    if index is not None:
                        current_item.move(index - 1)
                        self.update()
                        self.MODEL_UPDATED_SIGNAL.emit()
                        return
            # ctrl+down: move task down an index
            elif event.key() == QtCore.Qt.Key_Down:
                current_item = self._get_current_item()
                if current_item:
                    index = current_item.index()
                    if index is not None:
                        current_item.move(index + 1)
                        self.update()
                        self.MODEL_UPDATED_SIGNAL.emit()
                        return
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
                    if current_item.type == TaskType.ROUTINE:
                        current_item.change_task_type(TaskType.GENERAL)
                    elif current_item.type == TaskType.GENERAL:
                        current_item.change_task_type(TaskType.ROUTINE)
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
                    if type(current_item) == TaskCategory:
                        current_item.create_new_sibling_category()
                    elif type(current_item) == Task:
                        current_item.create_new_sibling_task()
                    self.update()
                    self.MODEL_UPDATED_SIGNAL.emit()

        super(Outliner, self).keyPressEvent(event)
