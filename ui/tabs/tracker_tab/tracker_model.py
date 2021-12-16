"""Timetable model."""

from PyQt5 import QtCore, QtGui, QtWidgets



class TrackerModel(QtCore.QAbstractItemModel):
    """Tracker model."""

    WEEKDAYS = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]

    def __init__(self, parent=None):
        """Initialise base tree model.

        Args:
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        super(TrackerModel, self).__init__(parent)
        self.num_cols = len(self.WEEKDAYS)
        self.num_rows = 1
        self.data = [
            [(i, j) for i in range(self.num_cols)]
            for j in range(self.num_rows)
        ]

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
            self.data[row][column]
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
        # return 1
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
        if role == QtCore.Qt.ItemDataRole.EditRole:
            return str(index.internalPointer())
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
            QtCore.Qt.ItemFlag.ItemIsEnabled | 
            QtCore.Qt.ItemFlag.ItemIsEditable
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
                return self.WEEKDAYS[section]
        return QtCore.QVariant()
