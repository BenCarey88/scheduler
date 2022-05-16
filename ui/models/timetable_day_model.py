"""Timetable day model."""


from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.common.date_time import Date


class BaseDayModel(QtCore.QAbstractItemModel):
    """Base model for day timetable."""
    TIME_INTERVAL = 1

    def __init__(self, calendar, calendar_day=None, parent=None):
        """Initialise calendar week model.

        Args:
            calendar (Calendar): the calendar this is using.
            calendar_day (CalendarDay or None): the calendar day this
                is modelling. If not given, use current day.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        super(BaseDayModel, self).__init__(parent)
        self.calendar_day = calendar_day or calendar.get_day(Date.now())
        self.num_rows = int(
            (Date.DAY_END - Date.DAY_START) / self.TIME_INTERVAL
        )
        self.num_cols = 1
        self.week_data = [
            [(i, j) for i in range(self.num_cols)]
            for j in range(self.num_rows)
        ]

    def set_calendar_day(self, calendar_day):
        """Set model to use given calendar day.

        Args:
            calendar_day (CalendarDay): calendar day to set to.
        """
        self.calendar_day = calendar_day
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
        return self.createIndex(
            row,
            column,
            self.week_data[row][column]
        )

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

        This is set to 1 in base class but can be overridden if needed.
        
        Returns:
            (int): number of columns.
        """
        return self.num_cols

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
        return (
            QtCore.Qt.ItemFlag.ItemIsEnabled # | 
            # QtCore.Qt.ItemFlag.ItemIsSelectable
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
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.calendar_day.header_name
        return QtCore.QVariant()
