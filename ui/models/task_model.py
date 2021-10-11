"""Tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task
from .base_tree_model import BaseTreeModel


class TaskModel(BaseTreeModel):
    """Task tree model.

    This model is intended to be used in the main panel of the Task Tab.
    """

    def __init__(self, root_tasks, parent=None):
        """Initialise task tree model.

        Args:
            root_tasks (list(Task)): list of root Task items.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        super(TaskModel, self).__init__(root_tasks, parent=parent)

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
        if index.column() == 1 and role == QtCore.Qt.DisplayRole:
            item = index.internalPointer()
            return item.status
        return super(TaskModel, self).data(index, role)
