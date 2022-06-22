"""Base dialog for creating and editing items."""

from functools import partial

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui import constants
from scheduler.ui.models.tree import ItemDialogTreeModel

from .base_tree_view import BaseTreeView


class ItemDialog(QtWidgets.QDialog):
    """Base dialog for creating and editing items."""

    def __init__(
            self,
            tree_manager,
            item_type_name,
            item=None,
            tree_item=None,
            parent=None):
        """Initialise dialog.

        Args:
            tree_manager (TreeManager): the task tree manager object.
            item (BaseScheduledItem, PlannedItem or None): item we're
                editing, if in edit mode. If None, we're in create mode.
            item_type_name (str): name of type of item this dialog deals with.
            tree_item (Task or None): tree item to initialize with, if we're
                not passing a scheduled item. If None, user has to choose.
            parent (QtWidgets.QWidget or None): parent widget, if one exists.
        """
        super(ItemDialog, self).__init__(parent=parent)
        self._tree_manager = tree_manager
        self._item = item
        self.is_editor = (item is not None)

        self.setWindowTitle("{0} Editor".format(item_type_name))
        flags = QtCore.Qt.WindowFlags(
            QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint
        )
        self.setWindowFlags(flags)

        outer_layout = QtWidgets.QHBoxLayout()
        left_layout = QtWidgets.QVBoxLayout()
        right_layout = QtWidgets.QVBoxLayout()
        self.main_layout = QtWidgets.QVBoxLayout()
        buttons_layout = QtWidgets.QHBoxLayout()
        left_layout.addLayout(self.main_layout)
        left_layout.addLayout(buttons_layout)
        left_layout.addStretch()
        outer_layout.addLayout(left_layout)
        outer_layout.addLayout(right_layout)
        self.setLayout(outer_layout)
        outer_layout.setStretch(0, 1)
        outer_layout.setStretch(1, 1)

        # tree layout
        self.tree_view = DialogTreeView(
            self._tree_manager,
            tree_item=(
                tree_item if tree_item is not None
                else item.tree_item if item is not None
                else None
            ),
            parent=self
        )
        right_layout.addWidget(self.tree_view)
        self.tree_view.MODEL_UPDATED_SIGNAL.connect(
            constants.SIGNALS.DIALOG_TREE_UPDATED_SIGNAL.emit
        )

        # button layout
        if self.is_editor:
            self.delete_button = QtWidgets.QPushButton(
                "Delete {0}".format(item_type_name)
            )
            buttons_layout.addWidget(self.delete_button)
            self.delete_button.clicked.connect(self.delete_item_and_close)
        accept_button_text = (
            "Edit {0}" if self.is_editor else "Add {0}"
        ).format(item_type_name)
        self.accept_button = QtWidgets.QPushButton(accept_button_text)
        buttons_layout.addWidget(self.accept_button)
        self.accept_button.clicked.connect(self.accept_and_close)
        self.accept_button.setFocus(True)

        self.tree_view.selectionModel().currentChanged.connect(
            self.update
        )

    def update(self):
        """Update view (to be reimplemented in subclasses)."""
        pass

    @property
    def tree_item(self):
        """Get tree item this is associated to.

        Returns:
            (BaseTreeItem or None): selected tree item, if one exists.
        """
        index = self.tree_view.currentIndex()
        if index is not None:
            return index.internalPointer()
        return None

    def accept_and_close(self):
        """Run add or modify scheduled item edit.

        This should be reimplemented in subclasses to deal with edits.

        Called when user clicks accept.
        """
        self.accept()
        self.close()

    def delete_item_and_close(self):
        """Run remove scheduled item edit.

        This should be reimplemented in subclasses to deal with edits.

        Called when user clicks delete.
        """
        self.reject()
        self.close()


class DialogTreeView(BaseTreeView):
    """Tree view to be used in item dialogs."""

    def __init__(self, tree_manager, tree_item=None, parent=None):
        """Initialise dialog tree view.

        Args:
            tree_manager (TreeManager): tree manager item.
            tree_item (BaseTreeItem or None): tree item to expand to.
            parent (QtGui.QWidget or None): QWidget parent of widget. 
        """
        super(DialogTreeView, self).__init__(tree_manager, parent=parent)
        self._is_full_tree = True
        self.setModel(ItemDialogTreeModel(tree_manager))
        self.tree_item = tree_item
        self.expanded_items = set()
        if self.tree_item is not None:
            self.expand_to_tree_item(self.tree_item, select=True)
        else:
            self.expand_to_top_level_tasks()
        self.selectionModel().currentChanged.connect(self.on_current_changed)
        self.expanded.connect(partial(self.mark_item_expanded, value=True))
        self.collapsed.connect(partial(self.mark_item_expanded, value=False))

    # TODO: should this go in the base class?
    def update(self):
        """Update view and keep selection."""
        expanded_items = set(self.expanded_items)
        current_item = self.tree_item
        self.expanded_items = set()
        self.setModel(ItemDialogTreeModel(self.tree_manager))
        self.MODEL_UPDATED_SIGNAL.emit()
        for item in expanded_items:
            self.expand_to_tree_item(item, expand_final=True)
        if current_item is not None and current_item.index() is not None:
            current_index = self.model().createIndex(
                self.tree_item.index(),
                0,
                self.tree_item
            )
            self.setCurrentIndex(current_index)
        self.viewport().update()

    def on_current_changed(self, new_index, old_index):
        """Callback for when current index is changed.

        Args:
            new_index (QtCore.QModelIndex): new index.
            old_index (QtCore.QModelIndex): previous index.
        """
        self.tree_item = self._get_current_item()

    def mark_item_expanded(self, index, value):
        """Mark item as expanded.

        Args:
            index (QtCore.QModelIndex): index of item.
            value (bool): whether or not the item has been expanded.
        """
        if index.isValid():
            item = index.internalPointer()
            if item:
                if value:
                    self.expanded_items.add(item)
                else:
                    self.expanded_items.discard(item)

    def expand_to_tree_item(self, tree_item, select=False, expand_final=False):
        """Expand to tree item.

        Args:
            tree_item (BaseTreeItem): tree item to expand to.
            select (bool): if True, also select item.
            expand_final (bool): if True, also expand the given item.
        """
        index = QtCore.QModelIndex()
        for ancestor_item in tree_item.iter_ancestors():
            self.expand(index)
            self.expanded_items.add(ancestor_item)
            row = ancestor_item.index()
            if row is not None:
                index = self.model().createIndex(
                    row,
                    0,
                    ancestor_item
                )
        if expand_final:
            self.expand(index)
        if select:
            self.setCurrentIndex(index)

    def expand_to_top_level_tasks(self, index=None):
        """Recursively expand view to top level tasks.

        Args:
            index (QtCore.QModelIndex): 
        """
        if index is None:
            index = QtCore.QModelIndex()
        task_item = index.internalPointer()
        if task_item is None:
            task_item = self.root
        if self.tree_manager.is_task(task_item):
            return
        self.expand(index)
        self.expanded_items.add(task_item)
        for i, _ in enumerate(task_item.get_all_children()):
            child_index = self.model().index(i, 0, index)
            self.expand_to_top_level_tasks(child_index)
