"""Base timetable model."""


from PyQt5 import QtCore, QtGui, QtWidgets


class BaseTimetableModel(QtCore.QAbstractTableModel):
    """Base model for all timetables."""
    TIME_INTERVAL = 1

    def __init__(
            self,
            calendar,
            calendar_period,
            num_rows,
            num_cols,
            parent=None):
        """Initialise calendar model.

        Args:
            calendar (Calendar): the calendar this is using.
            calendar_period (BaseCalendarPeriod): the calendar period this
                is modelling.
            num_rows (int): number of rows.
            num_cols (int): number of columns.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        super(BaseTimetableModel, self).__init__(parent)
        self.calendar = calendar
        self.calendar_period = calendar_period
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._data = [
            [(i, j) for i in range(self.num_cols)]
            for j in range(self.num_rows)
        ]

    def set_calendar_period(self, calendar_period):
        """Set model to use given calendar period.

        Args:
            calendar_period (CalendarPeriod): calendar period to set to.
        """
        self.calendar_period = calendar_period
        self.dataChanged.emit(QtCore.QModelIndex(), QtCore.QModelIndex())

    @staticmethod
    def convert_to_time(hour_float):
        """Convert float to time string.

        Args:
            hour_float (float): float representing time in hours.

        Returns:
            (str): formatted time.
        """
        decimal_part = hour_float % 1.0
        integer_part = int(hour_float - decimal_part)
        return "{0}:{1}".format(
            str(integer_part).zfill(2),
            str(int(decimal_part * 60)).zfill(2)
        )

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
            self._data[row][column]
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
        return QtCore.Qt.ItemFlag.ItemIsEnabled
