"""Planned items list model."""

from PyQt5 import QtCore, QtGui, QtWidgets


class PlannerListModel(QtCore.QAbstractListModel):
    """Model for planned items list."""

    def __init__(self, calendar_period, parent=None):
        """Initialise calendar model.

        Args:
            calendar (Calendar): the calendar this is using.
            calendar_period (BaseCalendarPeriod): the calendar period this
                is modelling.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        super(PlannerListModel, self).__init__(parent)
        self.calendar = calendar_period.calendar
        self.calendar_period = calendar_period
        self.columns = ["Item", "Importance", "Size"]

    def set_calendar_period(self, calendar_period):
        """Set model to use given calendar period.

        Args:
            calendar_period (CalendarPeriod): calendar period to set to.
        """
        self.calendar_period = calendar_period
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

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
        return self.num_rows

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
