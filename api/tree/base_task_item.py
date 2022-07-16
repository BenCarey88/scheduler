"""Base item for tasks and task categories."""

from collections import OrderedDict

from scheduler.api import constants
from scheduler.api.constants import TimePeriod

from scheduler.api.common.object_wrappers import (
    HostedDataList,
    MutableAttribute,
)
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
        # TODO: make all of these lists into HostedDataTimelines?
        self._planned_items = HostedDataList(
            pairing_id=constants.PLANNER_TREE_PAIRING,
            parent=self,
            driven=True,
        )
        self._scheduled_items = HostedDataList(
            pairing_id=constants.SCHEDULER_TREE_PAIRING,
            parent=self,
            filter=(lambda item: item.is_task()),
            driven=True,
        )

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
        if self.name in constants.TASK_COLORS:
            return constants.TASK_COLORS.get(self.name)
        if self.parent:
            return self.parent.color
        return None

    @property
    def scheduled_items(self):
        """Get scheduled items for given task.

        Returns:
            (list(ScheduledItem)): list of scheduled items.
        """
        return [item for item in self._scheduled_items if not item.is_repeat()]

    @property
    def repeat_scheduled_items(self):
        """Get repeat scheduled items for given task.

        Returns:
            (list(RepeatScheduledItem)): list of repeat scheduled items.
        """
        return [item for item in self._scheduled_items if item.is_repeat()]

    @property
    def planned_day_items(self):
        """Get planned day items for given task.

        Returns:
            (list(PlannedItems)): list of planned items.
        """
        return [
            item for item in self._planned_items
            if item.time_period == TimePeriod.DAY
        ]

    @property
    def planned_week_items(self):
        """Get planned week items for given task.

        Returns:
            (list(PlannedItems)): list of planned items.
        """
        return [
            item for item in self._planned_items
            if item.time_period == TimePeriod.WEEK
        ]

    @property
    def planned_month_items(self):
        """Get planned month items for given task.

        Returns:
            (list(PlannedItems)): list of planned items.
        """
        return [
            item for item in self._planned_items
            if item.time_period == TimePeriod.MONTH
        ]

    @property
    def planned_year_items(self):
        """Get planned year items for given task.

        Returns:
            (list(PlannedItems)): list of planned items.
        """
        return [
            item for item in self._planned_items
            if item.time_period == TimePeriod.YEAR
        ]
