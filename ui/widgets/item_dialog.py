"""Base dialog for creating and editing items."""


from collections import OrderedDict
from turtle import left
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.models.tree import ItemDialogTreeModel


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
        self.tree_view = QtWidgets.QTreeView(self)
        self.tree_view.setModel(ItemDialogTreeModel(self._tree_manager))
        if tree_item is not None:
            self.expand_to_and_select_tree_item(tree_item)
        elif item is not None and item.tree_item is not None:
            self.expand_to_and_select_tree_item(item.tree_item)
        else:
            self.expand_to_top_level_tasks()
        right_layout.addWidget(self.tree_view)

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

    def expand_to_and_select_tree_item(self, tree_item):
        """Expand to tree item in tree view.

        Args:
            tree_item (BaseTreeItem): tree item to expand to.
        """
        index = QtCore.QModelIndex()
        for ancestor_item in tree_item.iter_ancestors():
            self.tree_view.expand(index)
            row = ancestor_item.index()
            if row is not None:
                index = self.tree_view.model().createIndex(
                    ancestor_item.index(),
                    0,
                    ancestor_item
                )
        self.tree_view.setCurrentIndex(index)

    def expand_to_top_level_tasks(self, index=None):
        """Recursively expand view to top level tasks.

        Args:
            index (QtCore.QModelIndex): 
        """
        if index is None:
            index = QtCore.QModelIndex()
        task_item = index.internalPointer()
        if task_item is None:
            task_item = self._tree_manager.tree_root
        if self._tree_manager.is_task(task_item):
            return
        self.tree_view.expand(index)
        for i, _ in enumerate(task_item.get_all_children()):
            child_index = self.tree_view.model().index(i, 0, index)
            self.expand_to_top_level_tasks(child_index)

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
