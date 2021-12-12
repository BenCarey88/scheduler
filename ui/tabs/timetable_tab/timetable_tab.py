"""Timetable Tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.tabs.base_tab import BaseTab
from scheduler.ui import utils

from . timetable_model import TimetableModel

class TimetableTab(BaseTab):
    """Timetable tab."""

    def __init__(self, tree_root, tree_manager, outliner, parent=None):
        """Setup timetable main view.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            tree_manager (TreeManager): tree manager object.
            outliner (Outliner): outliner widget.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TimetableTab, self).__init__(
            tree_root,
            tree_manager,
            outliner,
            parent=parent
        )
        self.table = TimetableView()
        self.outer_layout.addWidget(self.table)

    def update(self):
        pass


class TimetableView(QtWidgets.QTableView):
    """Timetable view widget."""

    def __init__(self, parent=None):
        """Initialise task delegate item."""
        super(TimetableView, self).__init__(parent)
        self.setModel(TimetableModel(self))
        self.setItemDelegate(TimetableDelegate(self))
        #self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.resize_table()
        utils.set_style(self, "timetable.qss")

    def resize_table(self):
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

    def resizeEvent(self, event):
        super(TimetableView, self).resizeEvent(event)
        self.resize_table()

    def row_count(self):
        return self.model().rowCount(QtCore.QModelIndex())

    def column_count(self):
        return self.model().columnCount(QtCore.QModelIndex())


class TimetableDelegate(QtWidgets.QStyledItemDelegate):
    """Task Delegate for timetable."""

    def __init__(self, table, parent=None):
        """Initialise task delegate item."""
        super(TimetableDelegate, self).__init__(parent)
        self.table = table

    def sizeHint(self, option, index):
        """Get size hint for this item.

        Args:
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex): index of item.

        Returns:
            (QtCore.QSize): size hint.
        """
        num_rows = 12
        table_size = self.table.viewport().size()
        line_width = 1
        rows = self.table.row_count() or 1
        cols = self.table.column_count() or 1
        width = (table_size.width() - (line_width * (cols - 1))) / cols
        height = (table_size.height() -  (line_width * (rows - 1))) / num_rows
        return QtCore.QSize(width, height)

    def createEditor(self, parent, option, index):
        """Create editor widget for edit role.

        Overridding the default purely because this makes the line-edit
        cover the whole row which I like better.
        TODO: add same for outliner (and maybe move this to a BaseDelegate
        class that we can inherit from).

        Args:
            parent (QtWidgets.QWidget): parent widget.
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex) index of the edited item.

        Returns:
            (QtWidgets.QWidget): editor widget.
        """
        return super().createEditor(parent, option, index)

