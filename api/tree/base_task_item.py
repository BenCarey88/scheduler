"""Base item for tasks and task categories."""

from scheduler.api.constants import TASK_COLORS

from ._base_tree_item import BaseTreeItem


class BaseTaskItem(BaseTreeItem):
    """Base item for tasks and task categories."""

    # TODO: does this belong here?
    @property
    def color(self):
        """Get color of tree item.

        Returns:
            (tuple(int) or None): rgb color of item, if defined.
        """
        if self.name in TASK_COLORS:
            return TASK_COLORS.get(self.name)
        if self.parent:
            return self.parent.color
        return None

