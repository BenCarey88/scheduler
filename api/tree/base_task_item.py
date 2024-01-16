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


# TODO: give this a to_dict and from_dict method that subclasses can use
# maybe define _to_dict and _from_dict in subclasses and keep the non-
# underscored methods constant?
class BaseTaskItem(BaseTreeItem):
    """Base item for tasks and task categories."""
    DISPLAY_NAME_KEY = "display_name"
    COLOR_KEY = "color"
    ID_KEY = "id"

    def __init__(self, name, parent=None, color=None, display_name=""):
        """Initialise task item class.

        Args:
            name (str): name of tree item.
            parent (Task or None): parent of current item, if it's not a root.
            color (tuple(int) or None): rgb color tuple for item, if set.
            display_name (str): display name of task.
        """
        super(BaseTaskItem, self).__init__(name, parent)
        self._color = MutableAttribute(color, "color")
        self._display_name = MutableAttribute(display_name, "display_name")
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
        """Get color of task item.

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
    def display_name(self):
        """Get display name attribute of task item.

        Returns:
            (str): display name of item - this is the full name of the item,
                designed to identify it without needing the full path. If it's
                empty, its name will be used in place of this.
        """
        return self._display_name.value
    
    def get_display_name(self):
        """Get display name of task item.

        Returns:
            (str): the display_name property if it exists, otherwise the name
                attribute.
        """
        return self.display_name or self.name

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

    def to_dict(self):
        """Get json compatible dictionary representation of class.

        Note that this does not contain a name field, as the name is expected
        to be added as a key to this dictionary in the tasks json files.

        Returns:
            (OrderedDict): dictionary representation.
        """
        json_dict = {self.ID_KEY: self._get_id()}
        if self.display_name:
            json_dict[self.DISPLAY_NAME_KEY] = self.display_name
        if self._color.value is not None:
            json_dict[self.COLOR_KEY] = self.color
        return json_dict

    @classmethod
    def from_dict(cls, json_dict, name, parent=None, **kwargs):
        """Initialise class from dictionary representation.

        The json_dict is expected to be structured as described in the to_dict
        docstring.

        Args:
            json_dict (OrderedDict): dictionary representation.
            name (str): name of task.
            parent (Task, TaskCategory or None): parent of task.
            kwargs (dict): kwargs, passed from subclass definitions.

        Returns:
            (Task): task class for given dict.
        """
        display_name = json_dict.get(cls.DISPLAY_NAME_KEY, "")
        color = json_dict.get(cls.COLOR_KEY, None)
        task_item = cls(
            name=name,
            parent=parent,
            color=color,
            display_name=display_name,
            **kwargs,
        )
        task_item._activate()
        id = json_dict.get(cls.ID_KEY, None)
        if id is not None:
            # TODO: this bit means tasks are now added to the item registry.
            # This was done to make deserialization of task history dicts
            # work. Keep an eye on this, I want to make sure it doesn't slow
            # down loading too much.
            item_registry.register_item(id, task_item)

        return task_item
