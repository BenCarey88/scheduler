"""Task tree model."""

from PyQt5 import QtCore, QtGui, QtWidgets

from scheduler.api.tree.task import TaskStatus, TaskType

from scheduler.ui import constants
from ._base_tree_model import BaseTreeModel


class FullTaskTreeModel(BaseTreeModel):
    """Model for the full task tree."""

    def __init__(self, tree_manager, hide_filtered_items=False, parent=None):
        """Initialise task tree model.

        Args:
            tree_manager (TreeManager): tree manager item.
            parent (QtWidgets.QWidget or None): QWidget that this models.
            hide_filtered_items (bool): if True, use the child_filter from the
                tree manager to filter out all items whose checkboxes are
                deselected in the outliner.
        """
        super(FullTaskTreeModel, self).__init__(
            tree_manager,
            parent=parent
        )
