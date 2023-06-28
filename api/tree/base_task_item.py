"""Base item for tasks and task categories."""

from collections import OrderedDict

from scheduler.api import constants
from scheduler.api.enums import TimePeriod
from scheduler.api.serialization import item_registry

from scheduler.api.common.object_wrappers import (
    HostedDataList,
    MutableAttribute,
)
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
        # TODO: make this list into HostedDataTimeline?
        self._calendar_items = HostedDataList(
            pairing_id=constants.CALENDAR_ITEM_TREE_PAIRING,
            parent=self,
            filter=(lambda item: item.is_task()),
            driven=True,
        )
        self._id = None

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

    def _iter_planned_items(self):
        """Iterate over all planned items for given task.
        
        Yields:
            (PlannedItem): planned items.
        """
        for item in self._calendar_items:
            if item.is_planned_item:
                yield item

    def _iter_scheduled_items(self):
        """Iterate over all scheduled items for given task.

        Yields:
            (ScheduledItem): scheduled items.
        """
        for item in self._calendar_items:
            if item.is_scheduled_item:
                yield item

    @property
    def scheduled_items(self):
        """Get scheduled items for given task.

        Returns:
            (list(ScheduledItem)): list of scheduled items.
        """
        return [
            item for item in self._iter_scheduled_items()
            if not item.is_repeat()
        ]

    @property
    def repeat_scheduled_items(self):
        """Get repeat scheduled items for given task.

        Returns:
            (list(RepeatScheduledItem)): list of repeat scheduled items.
        """
        return [
            item for item in self._iter_scheduled_items()
            if item.is_repeat()
        ]

    @property
    def planned_day_items(self):
        """Get planned day items for given task.

        Returns:
            (list(PlannedItems)): list of planned items.
        """
        return [
            item for item in self._iter_planned_items()
            if item.time_period == TimePeriod.DAY
        ]

    @property
    def planned_week_items(self):
        """Get planned week items for given task.

        Returns:
            (list(PlannedItems)): list of planned items.
        """
        return [
            item for item in self._iter_planned_items()
            if item.time_period == TimePeriod.WEEK
        ]

    @property
    def planned_month_items(self):
        """Get planned month items for given task.

        Returns:
            (list(PlannedItems)): list of planned items.
        """
        return [
            item for item in self._iter_planned_items()
            if item.time_period == TimePeriod.MONTH
        ]

    @property
    def planned_year_items(self):
        """Get planned year items for given task.

        Returns:
            (list(PlannedItems)): list of planned items.
        """
        return [
            item for item in self._iter_planned_items()
            if item.time_period == TimePeriod.YEAR
        ]

    def _get_id(self):
        """Generate unique id for object.

        This should be used only during the serialization process, so that
        the data used for the id string is up to date. Note that once this
        is run the id string is fixed, allowing it to be referenced by other
        classes during serialization (see the item_registry module for
        more information on how this is done).

        Returns:
            (str): unique id.
        """
        if self._id is None:
            self._id = item_registry.generate_unique_id(self.path)
        return self._id
