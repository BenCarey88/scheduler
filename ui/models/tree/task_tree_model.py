"""Task tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.enums import ItemStatus
from scheduler.api.tree.task import TaskType

from scheduler.ui import constants
from ._base_tree_model import BaseTreeModel


class TaskTreeModel(BaseTreeModel):
    """Task tree model.

    This model is intended to be used in the main panel of the Task Tab.
    """
    STATUS_COLUMN = "Status"
    IMPORTANCE_COLUMN = "Importance"
    SIZE_COLUMN = "Size"

    def __init__(self, tree_manager, root_task, parent=None):
        """Initialise task tree model.

        Args:
            root_task (Task): root Task item.
            tree_manager (TreeManager): tree manager item.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        super(TaskTreeModel, self).__init__(
            tree_manager,
            tree_root=root_task,
            mime_data_format=constants.TASK_TAB_TREE_MIME_DATA_FORMAT,
            parent=parent,
        )
        self.columns = [
            self.NAME_COLUMN,
            self.STATUS_COLUMN,
            self.IMPORTANCE_COLUMN,
            self.SIZE_COLUMN,
        ]

    @property
    def child_filter(self):
        """Get child filter.

        Returns:
            (BaseTreeFilter): child filter, combining the initial filter
                passed during construction, and the item filter from the
                tree manager.
        """
        item_filter = self.tree_manager.child_filter
        if item_filter:
            return (self._base_filter & item_filter)
        return self._base_filter

    def data(self, index, role):
        """Get data for given item item and role.

        Args:
            index (QtCore.QModelIndex): index of item item.
            role (QtCore.Qt.Role): role we want data for.

        Returns:
            (QtCore.QVariant): data for given item and role.
        """
        column_name = self.get_column_name(index)
        if column_name is None:
            return QtCore.QVariant()

        # Item column
        if column_name == self.NAME_COLUMN:
            if role == QtCore.Qt.ItemDataRole.ForegroundRole:
                item = index.internalPointer()
                if item:
                    return constants.TASK_STATUS_COLORS.get(
                        item.status
                    )
            if role == QtCore.Qt.ItemDataRole.FontRole:
                item = index.internalPointer()
                if item:
                    font = QtGui.QFont()
                    if (item.status == ItemStatus.COMPLETE
                            or item.status == ItemStatus.IN_PROGRESS):
                        font.setBold(True)
                    if item.type == TaskType.ROUTINE:
                        font.setItalic(True)
                    return font

        # Status column
        if column_name == self.STATUS_COLUMN:
            if role == QtCore.Qt.ItemDataRole.CheckStateRole:
                item = index.internalPointer()
                if item:
                    return constants.TASK_STATUS_CHECK_STATES.get(
                        item.status
                    )

        # Importance Column
        if column_name in self.IMPORTANCE_COLUMN:
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                item = index.internalPointer()
                if item:
                    return item.importance
            if role == QtCore.Qt.ItemDataRole.ForegroundRole:
                item = index.internalPointer()
                if item:
                    return constants.TASK_IMPORTANCE_COLORS.get(
                        item.importance
                    )
            if role == QtCore.Qt.ItemDataRole.FontRole:
                item = index.internalPointer()
                if item:
                    font = QtGui.QFont()
                    font.setBold(True)
                    return font

        # Size Column
        if column_name in self.SIZE_COLUMN:
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                item = index.internalPointer()
                if item:
                    return item.size

        return super(TaskTreeModel, self).data(index, role)

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
        column_name = self.get_column_name(index)
        if column_name is None:
            return False
        if (column_name == self.STATUS_COLUMN and
                role == QtCore.Qt.ItemDataRole.CheckStateRole):
            task_item = index.internalPointer()
            if not task_item:
                return False
            return self.tree_manager.update_task(
                task_item,
                # TODO: start adding in the status overrides
                # status_override=True,
            )
        if role == QtCore.Qt.ItemDataRole.EditRole:
            if column_name == self.IMPORTANCE_COLUMN:
                task_item = index.internalPointer()
                if not task_item:
                    return False
                return self.tree_manager.modify_task(
                    task_item,
                    importance=value,
                )
            if column_name == self.SIZE_COLUMN:
                task_item = index.internalPointer()
                if not task_item:
                    return False
                return self.tree_manager.modify_task(
                    task_item,
                    size=value,
                )
        return super(TaskTreeModel, self).setData(index, value, role)

    def flags(self, index):
        """Get flags for given item item.

        Args:
            index (QtCore.QModelIndex): index of item item.

        Returns:
            (QtCore.Qt.Flag): Qt flags for item.
        """
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        flags = (
            QtCore.Qt.ItemFlag.ItemIsEnabled |
            QtCore.Qt.ItemFlag.ItemIsSelectable |
            QtCore.Qt.ItemFlag.ItemIsEditable
        )
        if self.get_column_name(index) == self.STATUS_COLUMN:
            return flags | QtCore.Qt.ItemFlag.ItemIsUserCheckable
        if (self.get_column_name(index) in
                (self.IMPORTANCE_COLUMN, self.SIZE_COLUMN)):
            return flags
        return super(TaskTreeModel, self).flags(index)
