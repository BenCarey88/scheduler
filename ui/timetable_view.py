"""TimetableView tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task
from .task_outliner import TaskOutliner


class TimetableView(QtWidgets.QWidget):
    """Timetable view tab."""

    def __init__(self, *args, **kwargs):
        """Initialise task view."""
        super(TimetableView, self).__init__(*args, **kwargs)

        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        self.table = QtWidgets.QTableWidget(3, 10)
        self.layout.addWidget(self.table)