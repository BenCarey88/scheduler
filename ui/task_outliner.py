"""TaskOutliner Panel."""

import os

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.task import Task
from scheduler.api.tasks_data import TaskData
from .task_model import TaskModel


class TaskOutliner(QtWidgets.QTreeView):
    """TaskOutliner panel."""

    def __init__(self, *args, **kwargs):
        """Initialise task view."""
        super(QtWidgets.QTreeView, self).__init__(*args, **kwargs)

        path = "C:\\Users\\benca\\OneDrive\\Documents\\Admin\\Scheduler\\tasks\\projects.json"
        self.tasks_data = TaskData.from_file(path)

        self.setModel(TaskModel(self.tasks_data.get_tasks(), self))
