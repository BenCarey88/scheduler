"""Abstract Base Tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.exceptions import DuplicateChildNameError


class BaseTreeModel(QtCore.QAbstractItemModel):
    """Base tree model."""

    def __init__(self, tree_roots, parent=None, filters=None):
        """Initialise base tree model.

        Args:
            tree_roots (list(scheduler.api.tree_items.BaseTreeItem)): model
                root items (these are assumed to all be siblings in some
                tree, although they don't need to actually be at the root
                of that tree).
            parent (QtWidgets.QWidget or None): QWidget that this models.
            filters (list(scheduler.api.tree.filters.BaseFilter)): filters
                for reducing number of children to consider.
        """
        # TESTING NEW ROOT
        self.root = tree_roots
        with self.root.filter_children(filters or []):
            self.tree_roots = self.root.get_all_children()

        # self.tree_roots = tree_roots
        self.child_filters = filters or []
        # first_item = next(iter(tree_roots), None)
        # if first_item:
        #     parent_item = first_item.parent
        #     if parent_item:
        #         # in case the given roots are missing some siblings, we need
        #         # a filter to remove the other siblings from consideration
        #         with parent_item.filter_children(self.child_filters):
        #             children_of_parent = parent_item.get_all_children()
        #         if children_of_parent != tree_roots:
        #             self.child_filters.append(
        #                 filters.RestrictToGivenChildren(
        #                     parent_item,
        #                     [item.name for item in tree_roots]
        #                 )
        #             )
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
            with parent_item.filter_children(self.child_filters):
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
        if parent_item == self.root:
            return QtCore.QModelIndex()
        # if parent_item in self.tree_roots:
        #     # print ("1")
        #     parent_item_row = self.tree_roots.index(parent_item)
        # else:
        #     # print ("2")
        #     parent_item_row = parent_item.index()
        # print ("\t", [a.name for a in self.tree_roots], parent_item.name, parent_item_row)
        parent_row = parent_item.index()
        if parent_row is not None:
            return self.createIndex(parent_row, 0, parent_item)
        return QtCore.QModelIndex()

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
        with parent_item.filter_children(self.child_filters):
            return parent_item.num_children()

    def columnCount(self, index):
        """Get number of columns of given item.

        This is set to 1 in base class but can be overridden if needed.
        
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
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            item = index.internalPointer()
            return item.name
        return QtCore.QVariant()
        # return self.get_item_role(item, role)

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
        if not index.isValid():
            return False
        if not value:
            # can't set tree item with empty name
            return False
        if index.column() != 0:
            # in base class, we can only set data on the name column
            return False
        item = index.internalPointer()
        if not item:
            return False
        try:
            item.name = value
            self.dataChanged.emit(index, index)
            # import pdb; pdb.set_trace()
            return True
        except DuplicateChildNameError:
            return False

    def flags(self, index):
        """Get flags for given item item.

        Args:
            index (QtCore.QModelIndex): index of item item.

        Returns:
            (QtCore.Qt.Flag): Qt flags for item.
        """
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return (
            QtCore.Qt.ItemFlag.ItemIsEnabled | 
            QtCore.Qt.ItemFlag.ItemIsSelectable |
            QtCore.Qt.ItemFlag.ItemIsEditable |
            QtCore.Qt.ItemFlag.ItemIsTristate
        )

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
