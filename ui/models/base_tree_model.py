"""Abstract Base Tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree import filters


class BaseTreeModel(QtCore.QAbstractItemModel):
    """Base tree model."""

    def __init__(self, tree_roots, parent=None, filters=None):
        """Initialise base tree model.

        Args:
            tree_roots (list(scheduler.api.tree_items.BaseTreeItem)): tree
                root items.
            parent (QtWidgets.QWidget or None): QWidget that this models.
            filters (list(scheduler.api.tree.filters.BaseFilter)): filters
                for reducing number of children to consider.
        """
        self.tree_roots = tree_roots
        self.child_filters = filters or []
        first_item = next(iter(tree_roots), None)
        if first_item:
            parent_item = first_item.parent
            if parent_item:
                with parent_item.filter_children(*self.child_filters):
                    children_of_parent = parent_item.get_all_children()
                if children_of_parent != tree_roots:
                    self.child_filters.append(
                        filters.RestrictToGivenChildren(
                            parent_item,
                            [item.name for item in tree_roots]
                        )
                    )
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
            # move filter inside the base tree class as a decorator maybe?
            # or maybe this way is still better?
            with parent_item.filter_children(*self.child_filters):
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
        parent_item = child_item.parent
        if not parent_item: # == self.tree_root:
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
        with parent_item.filter_children(*self.child_filters):
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
        if role == QtCore.Qt.DisplayRole:
            item = index.internalPointer()
            return item.name
        if role == QtCore.Qt.EditRole:
            item = index.internalPointer()
            return item.name
        return QtCore.QVariant()
        # return self.get_item_role(item, role)

    # def setData(self, column, value):
    #     """Set data at given column to given value.

    #     Implementing this method allows the tree model to be editable.

    #     Args:
    #         column (int): column we're setting data at.
    #         value (QtCore.QVariant): value to set for data.

    #     Returns:
    #         (bool): True if setting data was successful, else False.
    #     """
    #     # if column != 0:
    #     #     return False
    #     self.tree_roots = value
    #     return True

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
