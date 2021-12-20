"""Abstract Base Tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets


class BaseTreeModel(QtCore.QAbstractItemModel):
    """Base tree model."""

    def __init__(self, tree_roots, parent):
        """Initialise base tree model.
        
        Args:
            tree_roots (list(scheduler.api.tree_items.BaseTreeItem)): tree
                root items.
            parent (QtWidgets.QWidget): QWidget that this models.
        """
        self.tree_roots = tree_roots
        self.child_filter = None
        super(BaseTreeModel, self).__init__(parent)

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
            if 0 <= row < len(self.tree_roots):
                child_item = self.tree_roots[row]
            else:
                return QtCore.QModelIndex()
        else:
            parent_item = parent_index.internalPointer()
            with parent_item.filter_children(self.child_filter):
                child_item = parent_item.get_child_at_index(row)
        if child_item:
            return self.createIndex(row, column, child_item)
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
        child_item = index.internalPointer()
        if child_item in self.tree_roots:
            return QtCore.QModelIndex()
        parent_item = child_item.parent
        if not parent_item:
            return QtCore.QModelIndex()
        return self.createIndex(parent_item.index(), 0, parent_item)

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
            return len(self.tree_roots) # parent_item = self.tree_root
        #else:
        parent_item = parent_index.internalPointer()
        with parent_item.filter_children(self.child_filter):
            return parent_item.num_children()

    def columnCount(self, index):
        """Get number of columns of given item
        
        Returns:
            (int): number of columns.
        """
        return 1

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
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        item = index.internalPointer()
        return item.name
        # return self.get_item_role(item, role)

    def flags(self, index):
        """Get flags for given item item.

        Args:
            index (QtCore.QModelIndex): index of item item.

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
            section (int): row we want header data for.
            orientation (QtCore.Qt.Orientaion): orientation of widget.
            role (QtCore.Qt.Role): role we want header data for.

        Returns:
            (QtCore.QVariant): header data.
        """
        if (orientation == QtCore.Qt.Horizontal
                and role == QtCore.Qt.DisplayRole):
            return "Tasks" #self.tree_root.name
        return QtCore.QVariant()
