"""Tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task
from .base_tree_model import BaseTreeModel


class TaskModel(BaseTreeModel):
    """Task tree model."""

    def __init__(self, root_tasks, parent):
        """Initialise task tree model.
        
        Args:
            root_tasks (list(Task)): list of root Task items.
            parent (QtWidgets.QWidget): QWidget that this models.
        """
        tree_root = Task("Tasks")
        for task in root_tasks:
            tree_root.add_subtask(task)
        super(TaskModel, self).__init__(tree_root, parent)
