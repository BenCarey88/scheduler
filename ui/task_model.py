"""Tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.task import Task


class TaskModel(QtCore.QAbstractItemModel):
    """Task tree model."""

    def __init__(self, root_tasks, parent):
        """Initialise task tree model.
        
        Args:
            root_tasks (list(Task)): list of root Task items.
            parent (QtWidgets.QWidget): QWidget that this models.
        """
        self.tree_root = Task("Tasks")
        for task in root_tasks:
            self.tree_root.add_subtask(task)
        super(QtCore.QAbstractItemModel, self).__init__(parent)

    def index(self, row, column, parent_index):
        """Get index of child item of given parent at given row and column.
        
        Args:
            row (int): row index.
            column (int): column index.
            parent_index (QtCore.QModelIndex) parent QModelIndex.

        Returns:
            (QtCore.QModelIndex): child QModelIndex.
        """
        if not self.hasIndex(row, column, parent_index):
            return QtCore.QModelIndex()
        if not parent_index.isValid():
            parent_task = self.tree_root
        else:
            parent_task = parent_index.internalPointer()
        child_task = parent_task.get_subtask_at_index(row)
        if child_task:
            return self.createIndex(row, column, child_task)
        return QtCore.QModelIndex()

    def parent(self, index):
        """Get index of parent item of given child.
        
        Args:
            index (QtCore.QModelIndex) child QModelIndex.

        Returns:
            (QtCore.QModelIndex): parent QModelIndex.
        """
        if not index.isValid():
            return QtCore.QModelIndex()
        child_task = index.internalPointer()
        parent_task = child_task.parent
        if parent_task == self.tree_root:
            return QtCore.QModelIndex()
        return self.createIndex(parent_task.index(), 0, parent_task)

    def rowCount(self, parent_index):
        """Get number of children of given parent.
        
        Args:
            parent_index (QtCore.QModelIndex) parent QModelIndex.

        Returns:
            (int): number of children.
        """
        if parent_index.column() > 0:
            return 0
        if not parent_index.isValid():
            parent_task = self.tree_root
        else:
            parent_task = parent_index.internalPointer()
        return parent_task.num_subtasks()

    def columnCount(self, index):
        """Get number of columns of given task
        
        Returns:
            (int): number of columns.
        """
        return 1

    def data(self, index, role):
        """Get data for given task item and role.
        
        Args:
            index (QtCore.QModelIndex): index of task item.
            role (QtCore.Qt.Role): role we want data for.

        Returns:
            (QtCore.QVariant): data for given item and role.
        """
        if not index.isValid():
            return QtCore.QVariant()
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        item = index.internalPointer()
        return item.name

    def flags(self, index):
        """Get flags for given task item.

        Args:
            index (QtCore.QModelIndex): index of task item.

        Returns:
            (QtCore.Qt.Flag): Qt flags for item.
        """
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return QtCore.Qt.ItemIsEditable
        #return QtCore.QAbstractItemModel.flags(index)

    def headerData(self, section, orientation, role):
        """Get header data.
        
        Args:
            section (int): column we want header data for.
            orientation (QtCore.Qt.Orientaion): orientation of widget.
            role (QtCore.Qt.Role): role we want header data for.

        Returns:
            (QtCore.QVariant): header data.
        """
        if (orientation == QtCore.Qt.Horizontal
                and role == QtCore.Qt.DisplayRole):
            return self.tree_root.name
        return QtCore.QVariant()
