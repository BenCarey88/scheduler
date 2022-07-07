"""Abstract Base Tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui import constants, utils


class BaseTreeModel(QtCore.QAbstractItemModel):
    """Base tree model."""
    NAME_COLUMN = "Name"

    def __init__(
            self,
            tree_manager,
            tree_root=None,
            filters=None,
            mime_data_format=None,
            parent=None):
        """Initialise base tree model.

        Args:
            tree_manager (TreeManager): tree manager item, used to manage the
                ui specific attributes of the tree.
            tree_root (BaseTreeItem or None): model root tree item - if None,
                we use the TaskRoot item from the tree manager. We actually
                treat the given root's children as the roots of this model,
                but we pass in the parent of those children for easier
                calculations.
            filters (list(scheduler.api.tree.filters.BaseFilter)): filters
                for reducing number of children in model. These may be added
                to the filter from the tree_manager.
            mime_data_format (str or None): data format of any mime data
                created - if None, mimedata can't be created.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        super(BaseTreeModel, self).__init__(parent)
        self.tree_manager = tree_manager
        self.root = tree_manager.tree_root if tree_root is None else tree_root
        self._base_filters = filters or []
        self.columns = [self.NAME_COLUMN]
        self.mime_data_format = (
            mime_data_format or
            constants.OUTLINER_TREE_MIME_DATA_FORMAT
        )

    @property
    def child_filters(self):
        """Get child filters.

        Returns:
            (list(BaseFilter)): list of all filters - in base class this is
                the ones passed during initialization.
        """
        return self._base_filters

    def get_column_name(self, index):
        """Get name of column at index.

        This framework is designed to allow us to change the order
        of the columns. All checks for which column we're in should
        use this get_column_name method so that changing the order
        of self.columns will change the order of the columns in the
        model.

        Args:
            index (QtCore.QModelIndex or int): QModelIndex or column
                number to query.

        Returns:
            (str or None): name of column, if exists.
        """
        if isinstance(index, QtCore.QModelIndex) and index.isValid():
            col = index.column()
        elif isinstance(index, int):
            col = index
        else:
            return None
        if 0 <= col < len(self.columns):
            return self.columns[col]
        return None

    def get_index_from_item(self, item):
        """Get index and row for given tree item.

        Args:
            item (BaseTreeItem or None): tree item to get index for. For
                convenience, we allow passing None and just return None.

        Returns:
            (QtCore.QModelIndex or None): index for that item in the model,
                if found.
        """
        parent = item.parent
        if parent is None:
            return QtCore.QModelIndex()
        row = item.index()
        if row is not None:
            return self.createIndex(row, 0, item)
        return None

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
            tree_roots = self.root.get_filtered_children(self.child_filters)
            if 0 <= row < len(tree_roots):
                child_item = tree_roots[row]
            else:
                return QtCore.QModelIndex()
        else:
            parent_item = parent_index.internalPointer()
            if parent_item is None:
                return QtCore.QModelIndex()
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
        if not parent_index.isValid():
            return len(self.root.get_filtered_children(self.child_filters))
        if self.get_column_name(parent_index) != self.NAME_COLUMN:
            return 0
        parent_item = parent_index.internalPointer()
        with parent_item.filter_children(self.child_filters):
            return parent_item.num_children()

    def columnCount(self, index=None):
        """Get number of columns of given item.

        This is set to 1 in base class but can be overridden if needed.

        Args:
            index (QtCore.QModelIndex) index to check at.

        Returns:
            (int): number of columns.
        """
        return len(self.columns)

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
        if (self.get_column_name(index) == self.NAME_COLUMN and
                (role == QtCore.Qt.ItemDataRole.DisplayRole or
                 role == QtCore.Qt.ItemDataRole.EditRole)):
            item = index.internalPointer()
            if item:
                return item.name
        return QtCore.QVariant()

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
        if role != QtCore.Qt.ItemDataRole.EditRole:
            # can only do text edit role in base class
            return False
        if self.get_column_name(index) != self.NAME_COLUMN:
            # in base class, we can only set data on the name column
            return False
        if not value:
            # can't set tree item with empty name
            return False
        item = index.internalPointer()
        if not item:
            return False
        if self.tree_manager.set_item_name(item, value):
            # self.dataChanged.emit(index, index)
            return True
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
        flags = QtCore.Qt.ItemFlag.ItemIsEnabled
        if self.get_column_name(index) == self.NAME_COLUMN:
            flags |= (
                QtCore.Qt.ItemFlag.ItemIsEnabled | 
                QtCore.Qt.ItemFlag.ItemIsSelectable |
                QtCore.Qt.ItemFlag.ItemIsEditable
            )
            if self.mime_data_format is not None:
                flags |= (
                    QtCore.Qt.ItemFlag.ItemIsDragEnabled |
                    QtCore.Qt.ItemFlag.ItemIsDropEnabled
                )
        return flags

    def headerData(self, section, orientation, role):
        """Get header data.

        Args:
            section (int): row/column we want header data for.
            orientation (QtCore.Qt.Orientaion): orientation of widget.
            role (QtCore.Qt.Role): role we want header data for.

        Returns:
            (QtCore.QVariant): header data.
        """
        if (orientation == QtCore.Qt.Horizontal
                and role == QtCore.Qt.DisplayRole):
            return "Tasks"
        return QtCore.QVariant()

    def mimeTypes(self):
        """Get accepted mime data types.

        Returns:
            (list(str)): list of mime types.
        """
        return [self.mime_data_format] if self.mime_data_format else []

    def supportedDropAction(self):
        """Get supported drop action types:

        Return:
            (QtCore.Qt.DropAction): supported drop actions.
        """
        return (
            QtCore.Qt.DropAction.MoveAction |
            QtCore.Qt.DropAction.CopyAction
        )

    def mimeData(self, indexes):
        """Get mime data for given indexes.

        This is called at the 'drag' stage of drag and drop.

        Args:
            indexes (list(QtCore.QModelIndex)): list of indexes to get mime
                data for.

        Returns:
            (QtCore.QMimeData): mimedata for given indexes.
        """
        if self.mime_data_format is None:
            return QtCore.QMimeData()
        tree_items = [
            index.internalPointer()
            for index in indexes
            if index.isValid() and index.internalPointer()
        ]
        return utils.encode_mime_data(tree_items, self.mime_data_format)

    def canDropMimeData(self, mime_data, action, row, col, parent_index):
        """Check whether we can drop mime data over a given item.

        Args:
            mime_data (QtCore.QMimeData): mime data.
            action (QtCore.Qt.DropAction): the type of drop action being done.
            row (int): the row we're dropping on.
            column (int): the column we're dropping on.
            parent_index (QtCore.QModelIndex): index of parent item we're
                dropping under.

        Returns:
            (bool): True if we can drop the item, else False.
        """
        if not mime_data.hasFormat(self.mime_data_format):
            return False
        if self.get_column_name(col) not in [self.NAME_COLUMN, None]:
            return False
        parent = parent_index.internalPointer()
        if not parent:
            return False
        item = utils.decode_mime_data(mime_data, self.mime_data_format)
        if item is None:
            return False
        return self.tree_manager.can_accept_child(parent, item)

    def dropMimeData(self, data, action, row, column, parent_index):
        """Add mime data at given index.

        This is called at the 'drop' stage of drag and drop.

        Args:
            data (QtCore.QMimeData): mime data.
            action (QtCore.Qt.DropAction): the type of drop action being done.
            row (int): the row we're dropping on. If -1, this means that we're
                dropping directly on the parent item (interpreted as dropping
                it on the final row of that item).
            column (int): the column we're dropping on.
            parent_index (QtCore.QModelIndex): index of parent item we're
                dropping under.

        Returns:
            (bool): True if drop was successful, else False.
        """
        if action == QtCore.Qt.DropAction.IgnoreAction:
            return True
        parent = parent_index.internalPointer()
        if not parent:
            return False
        item = utils.decode_mime_data(data, self.mime_data_format, drop=True)
        if item is None:
            return False

        if row < 0:
            # if row is -1 this means we've dropped it on the parent,
            # add to end of row
            if parent_index.isValid():
                row = self.rowCount(parent_index)
            else:
                return False

        if item.parent == parent:
            # if item is being dropped further along its parents childlist
            # then row needs to be reduced by 1
            if row > item.index():
                row -= 1
        orig_row = item.index()
        if orig_row is None:
            return False

        return self.tree_manager.move_item(item, parent, row)

    def set_filters(self, new_filters, *args):
        """Set filters for model.

        Args:
            new_filters (list(BaseFilter)): filters to set.

        Returns:
            (bool): whether or not action was successful.
        """
        self.beginResetModel()
        self._base_filters = new_filters
        self.endResetModel()
        return True

    ### Callbacks ###
    def pre_item_added(self, item, parent, row):
        """Callback for before an item has been added.

        Args:
            item (BaseTreeItem): the item to add.
            parent (BaseTreeItem): the parent the item will be added under.
            row (int): the index the item will be added at.
        """
        parent_index = self.get_index_from_item(parent)
        if parent_index is not None:
            self.beginInsertRows(parent_index, row, row)
            self._insert_rows_in_progress = True

    def on_item_added(self, item, parent, row):
        """Callback for after an item has been added.

        Args:
            item (BaseTreeItem): the item that was added.
            parent (BaseTreeItem): the parent the item was added under.
            row (int): the index the item was added at.
        """
        if self._insert_rows_in_progress:
            self.endInsertRows()
            self._insert_rows_in_progress = False

    def pre_item_removed(self, item, parent, row):
        """Callbacks for before an item is removed.

        Args:
            item (BaseTreeItem): the item to remove.
            parent (BaseTreeItem): the parent of the removed item.
            row (int): the old index of the removed item in its
                parent's child list.
        """
        parent_index = self.get_index_from_item(parent)
        if parent_index is not None:
            self.beginRemoveRows(parent_index, row, row)
            self._remove_rows_in_progress = True

    def on_item_removed(self, item, parent, row):
        """Callback for after an item has been removed.

        Args:
            parent (BaseTreeItem): the parent of the removed item.
            index (int): the old index of the removed item in its
                parent's child list.
        """
        if self._remove_rows_in_progress:
            self.endRemoveRows()
            self._remove_rows_in_progress = False

    def pre_item_moved(self, item, old_parent, old_row, new_parent, new_row):
        """Callback for before an item is moved.

        Args:
            item (BaseTreeItem): the item to be moved.
            old_parent (BaseTreeItem): the original parent of the item.
            old_row (int): the original index of the item.
            new_parent (BaseTreeItem): the new parent of the moved item.
            new_row (int): the new index of the moved item.
        """
        old_parent_index = self.get_index_from_item(old_parent)
        new_parent_index = self.get_index_from_item(new_parent)
        if old_parent_index is not None and new_parent_index is not None:
            if old_parent == new_parent and new_row > old_row:
                new_row += 1
            self.beginMoveRows(
                old_parent_index,
                old_row,
                old_row,
                new_parent_index,
                new_row,
            )
            self._move_rows_in_progress = True

    def on_item_moved(self, item, old_parent, old_row, new_parent, new_row):
        """Callback for after an item has been moved.

        Args:
            item (BaseTreeItem): the item that was moved.
            old_parent (BaseTreeItem): the original parent of the item.
            old_row (int): the original index of the item.
            new_parent (BaseTreeItem): the new parent of the moved item.
            new_row (int): the new index of the moved item.
        """
        if self._move_rows_in_progress:
            self.endMoveRows()
            self._move_rows_in_progress = False

    def on_item_modified(self, old_item, new_item):
        """Callback for after an item has been modified.

        Args:
            old_item (BaseTreeItem): the item that was modified.
            new_item (BaseTreeItem): the item after modification.
        """
        index = self.get_index_from_item(old_item)
        if index is not None:
            self.dataChanged.emit(index, index)

    def remove_callbacks(self):
        """Deregister all callbacks for this model."""
        self.tree_manager.remove_callbacks(self)
