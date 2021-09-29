"""TimetableView tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task
from .task_outliner import TaskOutliner


class NextUpView(QtWidgets.QWidget):
    """Next up view tab (CHANGE NAME)"""

    def __init__(self, *args, **kwargs):
        """Initialise task view."""
        super(NextUpView, self).__init__(*args, **kwargs)

        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        self.view = QtWidgets.QWidget(self)
        self.layout.addWidget(self.view)
