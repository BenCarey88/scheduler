"""Timetable model."""

from PyQt5 import QtCore, QtGui, QtWidgets


class TimetableModel(QtCore.QAbstractItemModel):
    """Base tree model."""

    WEEKDAYS = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]
    DAY_START = 6
    DAY_END = 24
    TIME_INTERVAL = 1

    def __init__(self, parent=None):
        """Initialise base tree model.

        Args:
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        super(TimetableModel, self).__init__(parent)

    def index(self, row, column, parent_index):
        """Get index of child item of given parent at given row and column.

        Args:
            row (int): row index.
            column (int): column index.
            parent_index (QtCore.QModelIndex) parent QModelIndex.

        Returns:
            (QtCore.QModelIndex): child QModelIndex.
        """
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
        return (self.DAY_END - self.DAY_START) / self.TIME_INTERVAL

    def columnCount(self, index):
        """Get number of columns of given item.

        This is set to 1 in base class but can be overridden if needed.
        
        Returns:
            (int): number of columns.
        """
        return len(self.WEEKDAYS)

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

    def headerData(self, section, orientation, role):
        """Get header data.
        
        Args:
            section (int): row we want header data for.
            orientation (QtCore.Qt.Orientaion): orientation of widget.
            role (QtCore.Qt.Role): role we want header data for.

        Returns:
            (QtCore.QVariant): header data.
        """
        if role == QtCore.Qt.DisplayRole:
            if orientation == QtCore.Qt.Horizontal:
                return self.WEEKDAYS[section]
            else:
                hour_float = self.DAY_START + self.TIME_INTERVAL * section
                return self.convert_to_time(hour_float)
        return QtCore.QVariant()
