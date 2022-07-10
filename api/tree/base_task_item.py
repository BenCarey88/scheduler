"""Base item for tasks and task categories."""

from collections import OrderedDict

from scheduler.api.constants import TASK_COLORS

from scheduler.api.common.object_wrappers import MutableAttribute
from ._base_tree_item import BaseTreeItem


class BaseTaskItem(BaseTreeItem):
    """Base item for tasks and task categories."""
    ARCHIVE_ROOT_NAME = "ARCHIVE"

    def __init__(self, name, parent=None, color=None):
        """Initialise task item class.

        Args:
            name (str): name of tree item.
            parent (Task or None): parent of current item, if it's not a root.
            color (tuple(int) or None): rgb color tuple for item, if set.
        """
        super(BaseTaskItem, self).__init__(name, parent)
        self._color = MutableAttribute(color)
        # TODO: make all of these lists into Timelines?
        self._planned_year_items = []
        self._planned_month_items = []
        self._planned_week_items = []
        self._planned_day_items = []
        self._scheduled_items = []
        self._repeat_scheduled_items = []

    @property
    def is_archived(self):
        """Check if item is archived.

        Currently this finds the root each time this is called. I'm sure we
        can work an _is_archived attribute into the edits instead to avoid
        the unnecessary calculation.

        Returns:
            (bool): whether or not item is archived.
        """
        return (self.root.name == self.ARCHIVE_ROOT_NAME)

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

    @property
    def scheduled_items(self):
        """Get scheduled items for given task.

        Returns:
            (list(ScheduledItem)): list of scheduled items.
        """
        return [s.value for s in self._scheduled_items]

    @property
    def repeat_scheduled_items(self):
        """Get repeat scheduled items for given task.

        Returns:
            (list(RepeatScheduledItem)): list of repeat scheduled items.
        """
        return [s.value for s in self._repeat_scheduled_items]

    @property
    def planned_day_items(self):
        """Get planned day items for given task.

        Returns:
            (list(PlannedItems)): list of planned items.
        """
        return [p.value for p in self._planned_day_items]

    @property
    def planned_week_items(self):
        """Get planned week items for given task.

        Returns:
            (list(PlannedItems)): list of planned items.
        """
        return [p.value for p in self._planned_week_items]

    @property
    def planned_month_items(self):
        """Get planned month items for given task.

        Returns:
            (list(PlannedItems)): list of planned items.
        """
        return [p.value for p in self._planned_month_items]

    @property
    def planned_year_items(self):
        """Get planned year items for given task.

        Returns:
            (list(PlannedItems)): list of planned items.
        """
        return [p.value for p in self._planned_year_items]
