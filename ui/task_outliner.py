"""TaskOutliner Panel."""

import os

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.task_data import TaskData
from scheduler.api.tree.task_category import TaskCategory
from .models.task_category_model import TaskCategoryModel


class TaskOutliner(QtWidgets.QTreeView):
    """TaskOutliner panel."""

    def __init__(self, *args, **kwargs):
        """Initialise task view."""
        super(TaskOutliner, self).__init__(*args, **kwargs)

        path = "C:\\Users\\benca\\OneDrive\\Documents\\Admin\\Scheduler\\tasks\\projects.json"
        self.task_data = TaskData.from_file(path)

        self.setModel(TaskCategoryModel(self.task_data.get_root_data(), self))
