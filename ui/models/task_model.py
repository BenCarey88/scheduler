"""Task tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import TaskStatus, TaskType

from scheduler.ui import constants
from ._base_tree_model import BaseTreeModel


class TaskModel(BaseTreeModel):
    """Task tree model.

    This model is intended to be used in the main panel of the Task Tab.
    """

    def __init__(self, root_task, tree_manager, num_cols=2, parent=None):
        """Initialise task tree model.

        Args:
            root_task (Task): root Task item.
            tree_manager (TreeManager): tree manager item.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        self.num_cols = num_cols
        super(TaskModel, self).__init__(root_task, tree_manager, parent=parent)

    @property
    def child_filters(self):
        """Get child filters.

        Returns:
            (list(BaseFilter)): list of all filters, combining the initial
                filters passed during construction, and the id filter from
                the tree manager.
        """
        id_filter = self.tree_manager.child_filter
        if id_filter:
            return self._base_filters + [id_filter]
        return self._base_filters

    def columnCount(self, index):
        """Get number of columns of given item

        Returns:
            (int): number of columns.
        """
        return self.num_cols

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
            if role == QtCore.Qt.ItemDataRole.ForegroundRole:
                item = index.internalPointer()
                if item:
                    return constants.TASK_STATUS_COLORS.get(
                        item.status
                    )
            if role == QtCore.Qt.ItemDataRole.FontRole:
                item = index.internalPointer()
                if item:
                    if (item.status == TaskStatus.COMPLETE
                            or item.status == TaskStatus.IN_PROGRESS):
                        font = QtGui.QFont()
                        font.setBold(True)
                        return font
            if role == QtCore.Qt.ItemDataRole.FontRole:
                item = index.internalPointer()
                if item.type == TaskType.ROUTINE:
                    font = QtGui.QFont()
                    font.setItalic(True)
                    return font
        if index.column() == 1:
            if role == QtCore.Qt.ItemDataRole.CheckStateRole:
                item = index.internalPointer()
                if item:
                    return constants.TASK_STATUS_CHECK_STATES.get(
                        item.status
                    )
        return super(TaskModel, self).data(index, role)

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
        if index.column() == 1 and role == QtCore.Qt.CheckStateRole:
            if not index.isValid():
                return False
            task_item = index.internalPointer()
            if not task_item:
                return False
            # TODO: this should be property of task item rather than TaskStatus
            task_item.update_task()
            self.dataChanged.emit(index, index)
            return True
        return super(TaskModel, self).setData(index, value, role)

    def flags(self, index):
        """Get flags for given item item.

        Args:
            index (QtCore.QModelIndex): index of item item.

        Returns:
            (QtCore.Qt.Flag): Qt flags for item.
        """
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        if index.column() == 1:
            # TODO: work out how to create a selection of base flags
            # and then just add/remove some for each model subclass
            return (
                QtCore.Qt.ItemFlag.ItemIsEnabled |
                QtCore.Qt.ItemFlag.ItemIsSelectable |
                QtCore.Qt.ItemFlag.ItemIsEditable |
                QtCore.Qt.ItemFlag.ItemIsUserCheckable
            )
        return super(TaskModel, self).flags(index)
