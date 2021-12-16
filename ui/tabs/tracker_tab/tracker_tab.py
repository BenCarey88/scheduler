
from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task
from scheduler.ui.tabs.base_tab import BaseTab
from scheduler.ui import utils

from .tracker_model import TrackerModel


class TrackerTab(BaseTab):
    """Timetable tab."""

    def __init__(self, tree_root, tree_manager, outliner, parent=None):
        """Setup timetable main view.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            tree_manager (TreeManager): tree manager object.
            outliner (Outliner): outliner widget.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TrackerTab, self).__init__(
            tree_root,
            tree_manager,
            outliner,
            parent=parent
        )
        self.table = TrackerView(tree_root, tree_manager)
        self.outer_layout.addWidget(self.table)


class TrackerView(QtWidgets.QTableView):

    def __init__(self, tree_root, tree_manager, parent=None):
        """Initialise tracker delegate item."""
        super(TrackerView, self).__init__(parent)
        utils.set_style(self, "tracker.qss")
        model = TrackerModel()
        self.setModel(TrackerModel())
        self.setItemDelegate(TrackerDelegate(self))
        self.verticalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Fixed
        )
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.resize_table()
        self.open_editors()

    # TODO this page shares a lot of functionality with TimetableView - maybe
    # make a bunch of base classes to inherit from (same for the model)
    def resize_table(self):
        self.resizeRowsToContents()
        self.resizeColumnsToContents()

    def resizeEvent(self, event):
        super(TrackerView, self).resizeEvent(event)
        self.resize_table()
        self.open_editors()

    def open_editors(self):
        model = self.model()
        for i in range(model.num_rows):
            for j in range(model.num_cols):
                index = model.index(i, j, QtCore.QModelIndex())
                if index.isValid():
                    self.openPersistentEditor(index)

    def row_count(self):
        return self.model().rowCount(QtCore.QModelIndex())

    def column_count(self):
        return self.model().columnCount(QtCore.QModelIndex())


class TrackerDelegate(QtWidgets.QStyledItemDelegate):
    """Task Delegate for tracker."""

    # repeat of attrs from model (find way to share this info)
    WEEKDAYS = ["Sat", "Sun", "Mon", "Tue", "Wed", "Thu", "Fri"]

    def __init__(self, table, parent=None):
        """Initialise task delegate item."""
        super(TrackerDelegate, self).__init__(parent)
        self.table = table

    def sizeHint(self, option, index):
        """Get size hint for this item.

        Args:
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex): index of item.

        Returns:
            (QtCore.QSize): size hint.
        """
        table_size = self.table.viewport().size()
        line_width = 1
        rows = self.table.row_count() or 1
        cols = self.table.column_count() or 1
        width = (table_size.width() - (line_width * (cols - 1))) / cols
        height = (table_size.height() -  (line_width * (rows - 1))) / rows
        return QtCore.QSize(width, height)

    def createEditor(self, parent, option, index):
        """Create editor widget for edit role.

        Args:
            parent (QtWidgets.QWidget): parent widget.
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex) index of the edited item.

        Returns:
            (QtWidgets.QWidget): editor widget.
        """
        item = index.internalPointer()
        editor_widget = QtWidgets.QFrame(parent=parent)
        layout = QtWidgets.QVBoxLayout()
        editor_widget.setLayout(layout)
        for i in range(5):
            line_edit = QtWidgets.QLineEdit()
            line_edit.setText(str(item))
            layout.addWidget(line_edit)
        return editor_widget
        return super().createEditor(parent, option, index)
