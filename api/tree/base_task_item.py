"""Base item for tasks and task categories."""

from scheduler.api.constants import TASK_COLORS

from scheduler.api.common.object_wrappers import MutableAttribute
from ._base_tree_item import BaseTreeItem


class BaseTaskItem(BaseTreeItem):
    """Base item for tasks and task categories."""
    def __init__(self, name, parent=None, color=None):
        """Initialise task item class.

        Args:
            name (str): name of tree item.
            parent (Task or None): parent of current item, if it's not a root.
            color (tuple(int) or None): rgb color tuple for item, if set.
        """
        super(BaseTaskItem, self).__init__(name, parent)
        self._color = MutableAttribute(color)
        self._planned_year_items = []
        self._planned_month_items = []
        self._planned_week_items = []
        self._planned_day_items = []
        self._scheduled_items = []

    @property
    def color(self):
        """Get color of tree item.

        Returns:
            (tuple(int) or None): rgb color of item, if defined.
        """
        if self._color:
            return self._color.value
        if self.name in TASK_COLORS:
            return TASK_COLORS.get(self.name)
        if self.parent:
            return self.parent.color
        return None
