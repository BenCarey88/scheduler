"""Tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree import filters
from ._base_tree_model import BaseTreeModel


class TaskCategoryModel(BaseTreeModel):
    """Task category tree model.

    This model is to be used in the task outliner. It's intended to expand
    up to the first task items under each category but not show any subtasks.
    """

    def __init__(self, root_category, tree_manager, parent=None):
        """Initialise task category tree model.

        Args:
            root_category (TaskRoot): task root tree item.
            tree_manager (TreeManager): tree manager item.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        super(TaskCategoryModel, self).__init__(
            root_category,
            tree_manager,
            parent=parent,
            filters=[filters.NoSubtasks()]
        )

    def columnCount(self, index):
        """Get number of columns of given item
        
        Returns:
            (int): number of columns.
        """
        return 2

    def data(self, index, role):
        """Get data for given item item and role.

        Args:
            index (QtCore.QModelIndex): index of item item.
            role (QtCore.Qt.Role): role we want data for.

        Returns:
            (QtCore.QVariant): data for given item and role.
        """
        if not index.isValid():
            return QtCore.QVariant()
        if index.column() == 0:
            if role == QtCore.Qt.CheckStateRole:
                item = index.internalPointer()
                return not self.tree_manager.is_selected_for_filtering(item)
            if role == QtCore.Qt.ItemDataRole.ForegroundRole:
                item = index.internalPointer()
                if self.tree_manager.is_filtered_out(item):
                    return QtGui.QColor(150, 150, 150)
                else:
                    return QtGui.QColor(0, 0, 0)
        return super(TaskCategoryModel, self).data(index, role)

    def flags(self, index):
        """Get flags for given item item.

        Args:
            index (QtCore.QModelIndex): index of item item.

        Returns:
            (QtCore.Qt.Flag): Qt flags for item.
        """
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        if index.column() == 0:
            item = index.internalPointer()
            parent_item = item.parent
            if parent_item and self.tree_manager.is_filtered_out(parent_item):
                return (
                    QtCore.Qt.ItemFlag.ItemIsSelectable |
                    QtCore.Qt.ItemFlag.ItemIsEditable |
                    QtCore.Qt.ItemFlag.ItemIsUserCheckable
                )
            return (
                QtCore.Qt.ItemFlag.ItemIsEnabled |
                QtCore.Qt.ItemFlag.ItemIsSelectable |
                QtCore.Qt.ItemFlag.ItemIsEditable |
                QtCore.Qt.ItemFlag.ItemIsUserCheckable
            )
        return super(TaskCategoryModel, self).flags(index)

    def setData(self, index, value, role):
        """Set data at given index to given value.

        Implementing this method allows the tree model to be editable.

        Args:
            index (QtCore.QModelIndex): index of item we're setting data for.
            value (QtCore.QVariant): value to set for data.
            role (QtCore.Qt.Role): role we want to set data for.

        Returns:
            (bool): True if setting data was successful, else False.
        """
        if index.column() == 0 and role == QtCore.Qt.CheckStateRole:
            if not index.isValid():
                return False
            item = index.internalPointer()
            if not item:
                return False
            if self.tree_manager.is_selected_for_filtering(item):
                self.tree_manager.unfilter_item(item)
            else:
                self.tree_manager.filter_item(item)
            self.dataChanged.emit(index, index)
            return True
        return super(TaskCategoryModel, self).setData(index, value, role)
