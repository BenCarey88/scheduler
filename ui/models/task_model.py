"""Tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task
from ._base_tree_model import BaseTreeModel


class TaskModel(BaseTreeModel):
    """Task tree model.

    This model is intended to be used in the main panel of the Task Tab.
    """

    def __init__(self, root_task, tree_manager, parent=None):
        """Initialise task tree model.

        Args:
            root_task (Task): root Task item.
            tree_manager (TreeManager): tree manager item.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
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
