"""Task tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import TaskStatus, TaskType

from scheduler.ui import constants
from ._base_tree_model import BaseTreeModel


class FullTaskTreeModel(BaseTreeModel):
    """Model for the full task tree."""

    def __init__(self, tree_root, tree_manager, parent=None):
        """Initialise task tree model.

        Args:
            tree_root (TaskRoot): root Task item.
            tree_manager (TreeManager): tree manager item.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        super(FullTaskTreeModel, self).__init__(
            tree_root,
            tree_manager,
            parent=parent
        )
