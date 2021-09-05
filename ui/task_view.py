"""TaskView tab."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.task import Task
from .task_model import TaskModel
from .task_outliner import TaskOutliner


class TaskView(QtWidgets.QWidget):
    """TaskView tab."""

    def __init__(self, *args, **kwargs):
        """Initialise task view."""
        super(QtWidgets.QWidget, self).__init__(*args, **kwargs)

        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        self.outliner = TaskOutliner(self)
        self.layout.addWidget(self.outliner)

        self.main_view = QtWidgets.QWidget()
        self.layout.addWidget(QtWidgets.QWidget())
