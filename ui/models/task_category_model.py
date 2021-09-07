"""Tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import Task
from scheduler.api.tree.task_category import TaskCategory
from .base_tree_model import BaseTreeModel


class TaskCategoryModel(BaseTreeModel):
    """Task category tree model.

    This model is to be used in the task outliner. It's intended to expand
    up to the first task items under each category but not show any subtasks.
    To do this, we override the index and rowCount methods to ignore children
    of any items of type Task.
    """

    def __init__(self, root_categories, parent):
        """Initialise task category tree model.

        Args:
            root_categories (list(Task)): list of root TaskCategory items.
            parent (QtWidgets.QWidget): QWidget that this models.
        """
        tree_root = TaskCategory("Tasks")
        for category in root_categories:
            tree_root.add_child(category)
        super(TaskCategoryModel, self).__init__(tree_root, parent)
        self.child_filter = Task.NO_SUBTASKS_FILTER
