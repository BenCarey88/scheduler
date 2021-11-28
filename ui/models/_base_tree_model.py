"""Abstract Base Tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets
from scheduler.api.tree.task import Task
from scheduler.api.tree.task_category import TaskCategory

from scheduler.api.tree.exceptions import DuplicateChildNameError


class BaseTreeModel(QtCore.QAbstractItemModel):
    """Base tree model."""

    def __init__(self, tree_root, tree_manager, filters=None, parent=None):
        """Initialise base tree model.

        Args:
            tree_root (BaseTreeItem): model root tree item. We actually treat
                its children as the roots of this model, but we pass in the
                parent of those children for easier calculations.
            tree_manager (TreeManager): tree manager item, used to manage the
                ui specific attributes of the tree.
            filters (list(scheduler.api.tree.filters.BaseFilter)): filters
                for reducing number of children in model. These will be added
                to the filter from the tree_manager.
            parent (QtWidgets.QWidget or None): QWidget that this models.
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
        if (index.column() == 0 and 
                (role == QtCore.Qt.ItemDataRole.DisplayRole or
                 role == QtCore.Qt.ItemDataRole.EditRole)):
            item = index.internalPointer()
            if item:
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
            print ("CHANGING NAME OF", item.name, "to", value)
            item.name = value
            print ("NEW NAME IS", item.name)
            self.dataChanged.emit(index, index)
            print ("AND NOW NAME IS", item.name)
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
                QtCore.Qt.ItemFlag.ItemIsEditable |
                QtCore.Qt.ItemFlag.ItemIsDragEnabled |
                QtCore.Qt.ItemFlag.ItemIsDropEnabled
            )
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

    def mimeTypes(self):
        """Get accepted mime data types.

        Returns:
            (list(str)): list of mime types.
        """
        return ['application/vnd.treeviewdragdrop.list']

    def supportedDropAction(self):
        """Get supported drop action types:

        Return:
            (QtCore.Qt.DropAction): supported drop actions.
        """
        return QtCore.Qt.DropAction.MoveAction

    def mimeData(self, indexes):
        """Get mime data for given indexes.

        This is called at the 'drag' stage of drag and drop.

        Args:
            indexes (list(QtCore.QModelIndex)): list of indexes to get mime
                data for.

        Returns:
            (QtCore.QMimeData): mimedata for given indexes.
        """
        mimedata = QtCore.QMimeData()
        encoded_data = QtCore.QByteArray()
        stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.WriteOnly)
        if len(indexes) > 1:
            raise NotImplementedError(
                "Mime data currently only works for single index."
            )
        text = None
        for index in indexes:
            if index.isValid() and index.internalPointer():
                text = str(index.internalPointer().path)
        if text:
            stream << QtCore.QByteArray(text.encode('utf-8'))
            mimedata.setData(
                'application/vnd.treeviewdragdrop.list',
                encoded_data
            )
        return mimedata

    def canDropMimeData(self, mimeData, action, row, col, parent_index):
        """Check whether we can drop mime data over a given item.

        For now an item can be dropped UNLESS one of the following is true:
        - The item is an ancestor of the new parent
        - The parent has a child that is not the item but has the item's name
        - The item is a category and the parent is a task
        - The item is a subtask and the parent is a category
        - The parent is a top-level task (ie. a task that's not a subtask)

        The last 3 conditions ensure that we can't drop items from the outliner
        in the task tab and vice versa.

        Args:
            mimeData (QtCore.QMimeData): mime data.
            action (QtCore.Qt.DropAction): the type of drop action being done.
            row (int): the row we're dropping on.
            column (int): the column we're dropping on.
            parent_index (QtCore.QModelIndex): index of parent item we're
                dropping under.

        Returns:
            (bool): True if we can drop the item, else False.
        """
        # TODO: make separate method for decoding/encoding data.
        encoded_data = mimeData.data('application/vnd.treeviewdragdrop.list')
        stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.ReadOnly)
        while not stream.atEnd():
            byte_array = QtCore.QByteArray()
            stream >> byte_array
            encoded_path = bytes(byte_array).decode('utf-8')

        parent = parent_index.internalPointer()
        if not parent:
            return False
        root = parent.root

        item = root.get_item_at_path(encoded_path)
        if not item:
            return False

        if item.is_ancestor(parent):
            return False

        # TODO: wrap all this into a can_accept_child function in tree_manager

        # if it's a different parent but already has this kid name, no can do
        if (parent.id != item.parent.id 
                and item.name in parent._children.keys()):
            return False

        # TODO: for now I'm just assuming: subtasks are in taskview, non-subtasks
        # are in outliner. This is fine but I maybe something slightly neater
        # could be done with the tree_manager to ensure no crossover from outliner
        # to task view? Or maybe something better would be eg. encode model name/id
        # and check that the item being dropped matches it.
        if isinstance(parent, Task):
            # can't drop categories on tasks
            if isinstance(item, TaskCategory):
                return False
            # can't drop anything on top-level tasks
            if not parent.is_subtask():
                return False
        elif isinstance(parent, TaskCategory):
            # can't drop subtasks on categories
            if isinstance(item, Task) and item.is_subtask():
                return False

        return True

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
        if not data.hasFormat('application/vnd.treeviewdragdrop.list'):
            return False
        if column > 0:
            return False

        if row < 0:
            # if row is -1 this means we've dropped it on the parent,
            # add to end of row
            if parent_index.isValid():
                row = self.rowCount(parent_index)
            else:
                return False

        parent = parent_index.internalPointer()
        if not parent:
            return False
        # we need to use this for now rather that self.root bc in the task model
        # then the root is just the top-level task
        root = parent.root

        encoded_data = data.data('application/vnd.treeviewdragdrop.list')
        stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.ReadOnly)
        while not stream.atEnd():
            byte_array = QtCore.QByteArray()
            stream >> byte_array
            encoded_path = bytes(byte_array).decode('utf-8')

        item = root.get_item_at_path(encoded_path)
        if not item:
            return False

        # TODO: implement this as __eq__ for BaseTreeItem class
        if item.parent.id == parent.id:
            # if item is being dropped further along its parents childlist
            # then row needs to be reduced by 1
            if row > item.index():
                row -= 1

        self.beginResetModel()
        root.move_tree_item(encoded_path, parent.path, row)
        self.endResetModel()
        self.dataChanged.emit(parent_index, parent_index)
        return True
