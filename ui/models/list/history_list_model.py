"""History list model."""

from collections import OrderedDict

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.enums import ItemStatus
from scheduler.api.tree import TaskType, TaskHistory
from scheduler.ui import constants, utils


class HistoryListModel(QtCore.QAbstractItemModel):
    """Model for task history list."""

    def __init__(
            self,
            tree_manager,
            history_manager,
            calendar_day,
            use_long_names=False,
            parent=None):
        """Initialise calendar model.

        Args:
            tree_manager (TreeManager): the tree manager object.
            history_manager (HistoryManager): history manager object.
            calendar_day (CalendarDay): the calendar day this is modelling.
            use_long_names (bool): if True, use full path names for history
                items. Otherwise, we just use their task names.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        super(HistoryListModel, self).__init__(parent)
        self.tree_manager = tree_manager
        self.history_manager = history_manager
        self.calendar_day = calendar_day
        self.date = calendar_day.date
        self.use_long_names = use_long_names

    def index(self, row, column, parent_index):
        """Get index of child item of given parent at given row and column.

        Args:
            row (int): row index.
            column (int): column index.
            parent_index (QtCore.QModelIndex) parent QModelIndex.

        Returns:
            (QtCore.QModelIndex): child QModelIndex.
        """
        if self.hasIndex(row, column, parent_index):
            task_list = self.history_manager.get_filtered_tasks(
                self.calendar_day,
            )
            if 0 <= row < len(task_list):
                return self.createIndex(row, column, task_list[row])
        return QtCore.QModelIndex()

    def parent(self, index):
        """Get index of parent item of given child.

        Args:
            index (QtCore.QModelIndex) child QModelIndex.

        Returns:
            (QtCore.QModelIndex): parent QModelIndex.
        """
        return QtCore.QModelIndex()

    def rowCount(self, parent_index=None):
        """Get number of children of given parent.

        Args:
            parent_index (QtCore.QModelIndex or None) parent QModelIndex.

        Returns:
            (int): number of children.
        """
        return len(self.history_manager.get_filtered_tasks(self.calendar_day))

    def columnCount(self, parent_index=None):
        """Get number of columns of given item.

        Args:
            parent_index (QtCore.QModelIndex or None) parent QModelIndex.

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
        item = index.internalPointer()
        if not item:
            return QtCore.QVariant()

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if self.use_long_names:
                return item.path
            return item.name

        if role == QtCore.Qt.ItemDataRole.ForegroundRole:
            return constants.TASK_STATUS_COLORS.get(
                item.get_status_at_date(self.date)
            )

        if role == QtCore.Qt.ItemDataRole.FontRole:
            item = index.internalPointer()
            if item:
                status = item.get_status_at_date(self.date)
                font = QtGui.QFont()
                if (status == ItemStatus.COMPLETE
                        or status == ItemStatus.IN_PROGRESS):
                    font.setBold(True)
                if item.type == TaskType.ROUTINE:
                    font.setItalic(True)
                return font

        return QtCore.QVariant()

    def flags(self, index):
        """Get flags for given item item.

        Args:
            index (QtCore.QModelIndex): index of item item.

        Returns:
            (QtCore.Qt.Flag): Qt flags for item.
        """
        return (
            QtCore.Qt.ItemFlag.ItemIsEnabled |
            QtCore.Qt.ItemFlag.ItemIsSelectable |
            QtCore.Qt.ItemFlag.ItemIsDropEnabled
        )

    def mimeTypes(self):
        """Get accepted mime data types.

        Returns:
            (list(str)): list of mime types.
        """
        return [constants.OUTLINER_TREE_MIME_DATA_FORMAT]

    def supportedDropAction(self):
        """Get supported drop action types:

        Return:
            (QtCore.Qt.DropAction): supported drop actions.
        """
        return QtCore.Qt.DropAction.MoveAction

    def canDropMimeData(self, data, action, row, column, parent):
        """Check whether mime data can be dropped.

        Args:
            mimeData (QtCore.QMimeData): mime data.
            action (QtCore.Qt.DropAction): the type of drop action being done.
            row (int): the row we're dropping on.
            column (int): the column we're dropping on.
            parent_index (QtCore.QModelIndex): index of parent item we're
                dropping under.
        """
        # Only drop on empty spaces or between items
        if not parent.isValid():
            return True
        return False

    def dropMimeData(self, data, action, row, column, parent_index):
        """Add mime data at given index.

        This is called at the 'drop' stage of drag and drop.

        Args:
            data (QtCore.QMimeData): mime data.
            action (QtCore.Qt.DropAction): the type of drop action being done.
            row (int): the row we're dropping on. If -1, this means that we're
                dropping directly on the parent item (interpreted as dropping
                it on the final row).
            column (int): the column we're dropping on.
            parent_index (QtCore.QModelIndex): index of parent item we're
                dropping under.

        Returns:
            (bool): True if drop was successful, else False.
        """
        if action == QtCore.Qt.DropAction.IgnoreAction:
            return True
        if column > 0:
            return False

        if row < 0:
            # if row is -1 this means we've dropped it on the parent,
            # add to end of row
            row = self.rowCount(parent_index)

        if data.hasFormat(constants.OUTLINER_TREE_MIME_DATA_FORMAT):
            tree_item = utils.decode_mime_data(
                data,
                constants.OUTLINER_TREE_MIME_DATA_FORMAT,
                drop=True,
            )
            if tree_item is None:
                return False

            success = self.tree_manager.update_task(
                tree_item,
                date_time=self.date,
                status_override=True,
            )
            return bool(success)
