"""Tree model."""

from scheduler.api.tree import filters
from .base_tree_model import BaseTreeModel


class TaskCategoryModel(BaseTreeModel):
    """Task category tree model.

    This model is to be used in the task outliner. It's intended to expand
    up to the first task items under each category but not show any subtasks.
    """

    def __init__(self, root_categories, parent=None):
        """Initialise task category tree model.

        Args:
            root_categories (list(Task)): list of root TaskCategory items.
            parent (QtWidgets.QWidget or None): QWidget that this models.
        """
        super(TaskCategoryModel, self).__init__(
            root_categories,
            parent=parent,
            filters=[filters.NoSubtasks()]
        )

    def columnCount(self, index):
        """Get number of columns of given item
        
        Returns:
            (int): number of columns.
        """
        return 1
