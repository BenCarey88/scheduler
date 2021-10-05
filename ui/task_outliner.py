"""TaskOutliner Panel."""

import os

from PyQt5 import QtCore, QtGui, QtWidgets

from .models.task_category_model import TaskCategoryModel


class TaskOutliner(QtWidgets.QTreeView):
    """TaskOutliner panel."""

    def __init__(self, task_data, *args, **kwargs):
        """Initialise task view."""
        super(TaskOutliner, self).__init__(*args, **kwargs)

        self.task_data = task_data
        self.setModel(TaskCategoryModel(self.task_data.get_root_data(), self))
        self.setHeaderHidden(True)
        self.expandAll()
