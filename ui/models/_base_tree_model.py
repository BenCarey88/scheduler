"""Abstract Base Tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.exceptions import DuplicateChildNameError


class BaseTreeModel(QtCore.QAbstractItemModel):
    """Base tree model."""

    def __init__(self, tree_root, tree_manager, parent=None, filters=None):
        """Initialise base tree model.

        Args:
            tree_root (BaseTreeItem): model root tree item. We actually treat
                its children as the roots of this model, but we pass in the
                parent of those children for easier calculations.
            tree_manager (TreeManager): tree manager item, used to manage the
                ui specific attributes of the tree.
            parent (QtWidgets.QWidget or None): QWidget that this models.
            filters (list(scheduler.api.tree.filters.BaseFilter)): filters
                for reducing number of children in model. These will be added
                to the filter from the tree_manager.
        """
        # TODO: down the line is there an argument that everything should be
        # managed through the tree manager? ie. every other ui class should
        # call that instead of the Task, TaskCategory and TaskRoot items
        # directly? might mean a lot of repeated code though which is annoying
        # so not sure if it's the best option, will need to think, keeping
        # them as separate objects for now.
        self.root = tree_root
        self.tree_manager = tree_manager
        self._base_filters = filters or []
        with self.root.filter_children(self.child_filters):
            self.tree_roots = self.root.get_all_children()
        super(BaseTreeModel, self).__init__(parent)

    @property
    def child_filters(self):
        """Get child filters.

        Returns:
            (list(BaseFilter)): list of all filters - in base class this is
                the ones passed during initialization.
        """
        return self._base_filters

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
        if not parent_item:
            return QtCore.QModelIndex()
        if parent_item == self.root:
            return QtCore.QModelIndex()
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
            return len(self.tree_roots)
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
        if index.column() == 0 and role == QtCore.Qt.ItemDataRole.DisplayRole:
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
        if index.column() == 0:
            return (
                QtCore.Qt.ItemFlag.ItemIsEnabled | 
                QtCore.Qt.ItemFlag.ItemIsSelectable |
                QtCore.Qt.ItemFlag.ItemIsEditable
            )
        else:
            return QtCore.Qt.ItemFlag.ItemIsEnabled

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
            return "Tasks"
        return QtCore.QVariant()
