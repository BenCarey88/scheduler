"""Planned items list model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.calendar.planned_item import (
    PlannedItem,
    PlannedItemImportance,
    PlannedItemSize,
)
from scheduler.ui import constants, utils
from scheduler.ui.widgets.planned_item_dialog import PlannedItemDialog


class PlannerListModel(QtCore.QAbstractItemModel):
    """Model for planned items list."""
    NAME_COLUMN = "Name"
    PATH_COLUMN = "Path"
    IMPORTANCE_COLUMN = "Importance"
    SIZE_COLUMN = "Size"

    def __init__(
            self,
            tree_manager,
            planner_manager,
            calendar_period=None,
            time_period=None,
            open_dialog_on_drop_event=False,
            parent=None):
        """Initialise calendar model.

        Args:
            tree_manager (TreeManager): the tree manager object.
            planner_manager (PlannerManager): the planner manager object.
            calendar_period (BaseCalendarPeriod or None): the calendar
                period this is modelling.
            time_period (PlannedItemTimePeriod): the time period type this
                is modelling, if calendar_period not given.
            open_dialog_on_drop_event (bool): if True, use PlannedItemDialog
                to add dropped items, otherwise add directly.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        if calendar_period is None and time_period is None:
            raise Exception(
                "calendar_period and time_period args can't both be empty."
            )
        super(PlannerListModel, self).__init__(parent)
        self.tree_manager = tree_manager
        self.planner_manager = planner_manager
        self.calendar = planner_manager.calendar
        if calendar_period is None:
            calendar_period = self.calendar.get_current_period(time_period)
        self.calendar_period = calendar_period
        self.columns = [
            self.NAME_COLUMN,
            self.PATH_COLUMN,
            self.IMPORTANCE_COLUMN,
            self.SIZE_COLUMN,
        ]
        self.open_dialog_on_drop_event = open_dialog_on_drop_event

    def set_calendar_period(self, calendar_period):
        """Set model to use given calendar period.

        Args:
            calendar_period (CalendarPeriod): calendar period to set to.
        """
        self.calendar_period = calendar_period
        self.beginResetModel()
        self.endResetModel()
        # self.insertRows(0, len(self.calendar_period._planned_items))
        # self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    def get_column_name(self, index):
        """Get name of column at index.

        This framework is designed to allow us to change the order
        of the columns. All checks for which column we're in should
        use this get_column_name method so that changing the order
        of self.columns will change the order of the columns in the
        model.

        Args:
            index (int or QtCore.QModelIndex): column number or index to query.

        Returns:
            (str or None): name of column, if exists.
        """
        if isinstance(index, QtCore.QModelIndex):
            if not index.isValid():
                return None
            column = index.column()
        elif isinstance(index, int):
            column = index
        else:
            raise Exception("get_column_name requires QModelIndex or int")
        if 0 <= column < len(self.columns):
            return self.columns[column]
        return None

    def remove_item(self, index, force=False):
        """Remove item at given index.

        Args:
            index (QtCore.QModelIndex): index of item to remove.
            force (bool): if True, don't check with user before removing.

        Returns:
            (bool): whether or not removal was successful.
        """
        if index.isValid():
            item = index.internalPointer()
            if item is not None:
                continue_deletion = force or utils.simple_message_dialog(
                    "Delete Planned Item ({0})?".format(item.name),
                )
                if continue_deletion:
                    self.beginRemoveRows(
                        QtCore.QModelIndex(),
                        index.row(),
                        index.row(),
                    )
                    success = self.planner_manager.remove_planned_item(item)
                    self.endRemoveRows()
                    return success
        return False

    def sort(self, column, order):
        """Sort items in view based on given column.

        Args:
            column (int): column to sort by.
            order (QtCore.Qt.SortOrder): whether to sort forward or in
                reverse.
        """
        reverse = (order == QtCore.Qt.SortOrder.AscendingOrder)
        column_name = self.get_column_name(column)
        if column_name == self.NAME_COLUMN:
            key = lambda item : item.name
        elif column_name == self.PATH_COLUMN:
            key = lambda item : item.tree_path
        elif column_name == self.IMPORTANCE_COLUMN:
            key = lambda item : PlannedItemImportance.key(item.importance)
        elif column_name == self.SIZE_COLUMN:
            key = lambda item : PlannedItemSize.key(item.size)
        self.beginResetModel()
        self.planner_manager.sort_planned_items(
            self.calendar_period,
            key=key,
            reverse=reverse,
        )
        self.endResetModel()
        super(PlannerListModel, self).sort(column, order)

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
            item_list = self.calendar_period.get_planned_items_container()
            if 0 <= row < len(item_list):
                return self.createIndex(row, column, item_list[row])
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
        return len(self.calendar_period.get_planned_items_container())

    def columnCount(self, parent_index=None):
        """Get number of columns of given item.

        Args:
            parent_index (QtCore.QModelIndex or None) parent QModelIndex.

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
        item = index.internalPointer()
        if not item:
            return QtCore.QVariant()
        text_roles = [
            QtCore.Qt.ItemDataRole.DisplayRole,
            QtCore.Qt.ItemDataRole.EditRole,
        ]
        if role in text_roles:
            column_name = self.get_column_name(index)
            return {
                self.NAME_COLUMN: item.name,
                self.PATH_COLUMN: item.tree_path,
                self.IMPORTANCE_COLUMN: item.importance,
                self.SIZE_COLUMN: item.size,
            }.get(column_name)
        return QtCore.QVariant()

    def setData(self, index, value, role):
        """Set data at given index to given value.

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
        planned_item = index.internalPointer()
        if planned_item is None:
            return False
        if self.get_column_name(index) == self.IMPORTANCE_COLUMN:
            self.planner_manager.modify_planned_item(
                planned_item,
                importance=value,
            )
            self.dataChanged.emit(index, index)
            return True
        if self.get_column_name(index) == self.SIZE_COLUMN:
            self.planner_manager.modify_planned_item(
                planned_item,
                size=value,
            )
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, section, orientation, role):
        """Get header data.

        Args:
            section (int): row/column we want header data for.
            orientation (QtCore.Qt.Orientaion): orientation of widget.
            role (QtCore.Qt.Role): role we want header data for.

        Returns:
            (QtCore.QVariant): header data.
        """
        if orientation == QtCore.Qt.Orientation.Horizontal:
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                if 0 <= section < len(self.columns):
                    return self.columns[section]
        return QtCore.QVariant()

    def flags(self, index):
        """Get flags for given item item.

        Args:
            index (QtCore.QModelIndex): index of item item.

        Returns:
            (QtCore.Qt.Flag): Qt flags for item.
        """
        if self.get_column_name(index) == self.NAME_COLUMN:
            return (
                QtCore.Qt.ItemFlag.ItemIsEnabled |
                QtCore.Qt.ItemFlag.ItemIsSelectable |
                QtCore.Qt.ItemFlag.ItemIsDragEnabled |
                QtCore.Qt.ItemFlag.ItemIsDropEnabled
            )
        if (self.get_column_name(index) in 
                [self.IMPORTANCE_COLUMN, self.SIZE_COLUMN]):
            return (
                QtCore.Qt.ItemFlag.ItemIsEnabled |
                QtCore.Qt.ItemFlag.ItemIsSelectable |
                QtCore.Qt.ItemFlag.ItemIsEditable |
                QtCore.Qt.ItemFlag.ItemIsDropEnabled
            )
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
        return [
            constants.OUTLINER_TREE_MIME_DATA_FORMAT,
            constants.PLANNED_ITEM_MIME_DATA_FORMAT,
        ]

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
                "Mime data currently only works for single item."
            )
        text = None
        for index in indexes:
            if index.isValid() and index.internalPointer():
                text = index.internalPointer().get_temp_id()
        if text:
            stream << QtCore.QByteArray(text.encode('utf-8'))
            mimedata.setData(
                constants.PLANNED_ITEM_MIME_DATA_FORMAT,
                encoded_data
            )
        return mimedata

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

        root = self.planner_manager.tree_root

        if data.hasFormat(constants.OUTLINER_TREE_MIME_DATA_FORMAT):
            encoded_data = data.data(constants.OUTLINER_TREE_MIME_DATA_FORMAT)
            stream = QtCore.QDataStream(
                encoded_data,
                QtCore.QIODevice.ReadOnly
            )
            while not stream.atEnd():
                byte_array = QtCore.QByteArray()
                stream >> byte_array
                encoded_path = bytes(byte_array).decode('utf-8')

            tree_item = root.get_item_at_path(encoded_path)
            if tree_item is None:
                return False

            self.beginResetModel()
            if self.open_dialog_on_drop_event:
                dialog = PlannedItemDialog(
                    self.tree_manager,
                    self.planner_manager,
                    self.calendar_period,
                    tree_item=tree_item,
                    index=row,
                )
                success = dialog.exec()
            else:
                success = self.planner_manager.create_planned_item(
                    self.calendar,
                    self.calendar_period,
                    tree_item,
                    index=row,
                )
            self.endResetModel()
            return bool(success)

        elif data.hasFormat(constants.PLANNED_ITEM_MIME_DATA_FORMAT):
            encoded_data = data.data(constants.PLANNED_ITEM_MIME_DATA_FORMAT)
            stream = QtCore.QDataStream(
                encoded_data,
                QtCore.QIODevice.ReadOnly
            )
            while not stream.atEnd():
                byte_array = QtCore.QByteArray()
                stream >> byte_array
                encoded_id = bytes(byte_array).decode('utf-8')

            planned_item = PlannedItem.from_temp_id(encoded_id)
            if planned_item is None:
                return False

            self.beginResetModel()
            success = self.planner_manager.move_planned_item(
                planned_item,
                row,
            )
            self.endResetModel()
            return bool(success)
