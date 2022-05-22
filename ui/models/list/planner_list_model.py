"""Planned items list model."""

from PyQt5 import QtCore, QtGui, QtWidgets


class PlannerListModel(QtCore.QAbstractItemModel):
    """Model for planned items list."""
    NAME_COLUMN = "Name"
    IMPORTANCE_COLUMN = "Importance"
    SIZE_COLUMN = "Size"

    def __init__(
            self,
            calendar,
            calendar_period=None,
            time_period=None,
            parent=None):
        """Initialise calendar model.

        Args:
            calendar (Calendar): the calendar this is using.
            calendar_period (BaseCalendarPeriod or None): the calendar
                period this is modelling.
            time_period (PlannedItemTimePeriod): the time period type this
                is modelling, if calendar_period not given.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        if calendar_period is None and time_period is None:
            raise Exception(
                "calendar_period and time_period args can't both be empty."
            )
        super(PlannerListModel, self).__init__(parent)
        self.calendar = calendar
        if calendar_period is None:
            calendar_period = calendar.get_current_period(time_period)
        self.calendar_period = calendar_period
        self.columns = [
            self.NAME_COLUMN,
            self.IMPORTANCE_COLUMN,
            self.SIZE_COLUMN
        ]

    def set_calendar_period(self, calendar_period):
        """Set model to use given calendar period.

        Args:
            calendar_period (CalendarPeriod): calendar period to set to.
        """
        self.calendar_period = calendar_period
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    def get_column_name(self, index):
        """Get name of column at index.

        This framework is designed to allow us to change the order
        of the columns. All checks for which column we're in should
        use this get_column_name method so that changing the order
        of self.columns will change the order of the columns in the
        model.

        Args:
            index (QtCore.QModelIndex): index to query.

        Returns:
            (str or None): name of column, if exists.
        """
        if index.isValid() and 0 <= index.column() < len(self.columns):
            return self.columns[index.column()]
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

    def rowCount(self, parent_index):
        """Get number of children of given parent.

        Args:
            parent_index (QtCore.QModelIndex) parent QModelIndex.

        Returns:
            (int): number of children.
        """
        return len(self.calendar_period.get_planned_items_container())

    def columnCount(self, index):
        """Get number of columns of given item.

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
        return False

    def flags(self, index):
        """Get flags for given item item.

        Args:
            index (QtCore.QModelIndex): index of item item.

        Returns:
            (QtCore.Qt.Flag): Qt flags for item.
        """
        return QtCore.Qt.ItemFlag.ItemIsEnabled

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
