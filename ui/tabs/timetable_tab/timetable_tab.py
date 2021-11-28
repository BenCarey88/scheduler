"""Timetable Tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.tabs.base_tab import BaseTab

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
        self.table = TimeTableView()
        self.table.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding
        )
        self.outer_layout.addWidget(self.table)

    def update(self):
        pass


class TimeTableView(QtWidgets.QTableView):
    """Timetable view widget."""

    def __init__(self, parent=None):
        """Initialise task delegate item."""
        super(TimeTableView, self).__init__(parent)
        self.setModel(TimetableModel(self))


class TaskDelegate(QtWidgets.QStyledItemDelegate):
    """Task Delegate for task widget tree."""

    def __init__(self, parent=None):
        """Initialise task delegate item."""
        super(TaskDelegate, self).__init__(parent)

    def sizeHint(self, option, index):
        """Get size hint for this item.

        Args:
            option (QtWidgets.QStyleOptionViewItem): style options object.
            index (QtCore.QModelIndex): index of item.

        Returns:
            (QtCore.QSize): size hint.
        """
        

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
        if index.isValid():
            if index.column() == 0:
                item = index.internalPointer()
                if item:
                    editor = QtWidgets.QLineEdit(parent)
                    editor.setText(item.name)
                    return editor
        return super().createEditor(parent, option, index)
