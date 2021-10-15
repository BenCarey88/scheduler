"""Timetable Tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.ui.tabs.base_tab import BaseTab


class TimetableTab(BaseTab):
    """Timetable tab."""

    def __init__(self, tree_root, parent=None):
        """Setup timetable main view.

        Args:
            tree_root (BaseTreeItem): tree root item for tab's models.
            parent (QtGui.QWidget or None): QWidget parent of widget.
        """
        super(TimetableTab, self).__init__(tree_root, parent)

        self.table = QtWidgets.QTableWidget(3, 10)
        self.addWidget(self.table)

    def update(self):
        pass
