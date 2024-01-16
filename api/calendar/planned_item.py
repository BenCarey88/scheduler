"""Planned item class."""

from scheduler.api.common.object_wrappers import MutableAttribute
from scheduler.api.serialization import item_registry
from scheduler.api.tree import Task
from scheduler.api.utils import fallback_value
from ._base_calendar_item import BaseCalendarItem


class PlannedItemError(Exception):
    """Generic exception for planned item errors."""


class PlannedItem(BaseCalendarItem):
    """Class for items in planner tab."""
    TREE_ITEM_KEY = "tree_item"
    TIME_PERIOD_KEY = "time_period"

    def __init__(self, calendar, calendar_period, tree_item=None, **kwargs):
        """Initialize class.

        Args:
            calendar (Calendar): calendar object.
            calendar_period (BaseCalendarPeriod): calendar period this is
                associated to.
            tree_item (BaseTaskItem or None): the task item, if given.
            kwargs (dict): additional keyword arguments to pass to subclass
                init. This includes things like, status, update policies and
                name.
        """
        super(PlannedItem, self).__init__(
            calendar,
            tree_item=tree_item,
            **kwargs,
        )
        self._is_planned_item = True
        self._calendar_period = MutableAttribute(
            calendar_period,
            "calendar_period",
        )

    @property
    def calendar(self):
        """Get calendar object.

        Returns:
            (Calendar): the calendar object.
        """
        return self._calendar

    @property
    def calendar_period(self):
        """Get calendar period that item is planned for.

        Returns:
            (BaseCalendarPeriod): period that item is planned for.
        """
        return self._calendar_period.value

    @property
    def time_period(self):
        """Get time period type that item is planned for.

        Returns:
            (TimePeriod): period type item is planned for.
        """
        return self.calendar_period.get_time_period_type()

    @property
    def tree_path(self):
        """Get path of tree item.

        Returns:
            (str): path of tree item.
        """
        if self.tree_item:
            return self.tree_item.path
        return ""

    @property
    def start_date(self):
        """Get start date for planned item.

        Returns:
            (Date): start date.
        """
        return self.calendar_period.start_date

    @property
    def end_date(self):
        """Get end date for planned item.

        Returns:
            (Date): end date.
        """
        return self.calendar_period.end_date

    @property
    def status(self):
        """Get status of item.

        Returns:
            (ItemStatus): status of item.
        """
        return self._status.value

    @property
    def defunct(self):
        """Override defunct property.

        Returns:
            (bool): whether or not item should be considered deleted.
        """
        return super(PlannedItem, self).defunct or (self.tree_item is None)

    @property
    def scheduled_items(self):
        """Get scheduled items associated to this one.

        Returns:
            (list(BaseScheduledItem)): associated scheduled items.
        """
        return [
            child for child in self._children if child.is_scheduled_item
        ]

    @property
    def planned_children(self):
        """Get child planned items associated to this one.

        Returns:
            (list(PlannedItem))): associated child items.
        """
        return [
            child for child in self._children if child.is_planned_item
        ]

    @property
    def planned_parents(self):
        """Get parent items associated to this one.

        For now, all parents must be planned items, so this doesn't bother
        with filtering.

        Returns:
            (list(PlannedItem))): associated parent items.
        """
        return self._parents

    def __lt__(self, item):
        """Check if self is over a smaller period than other item.

        Args:
            item (PlannedItem): item to compare to.
        """
        if not isinstance(item, PlannedItem):
            raise PlannedItemError(
                "Cannot compare planned item with object of type {0}".format(
                    item.__class__.__name__
                )
            )
        return (
            self.time_period < item.time_period
        )

    def __le__(self, item):
        """Check if self is over a smaller or equal time period to other item.

        Args:
            item (PlannedItem): item to compare to.
        """
        if not isinstance(item, PlannedItem):
            raise PlannedItemError(
                "Cannot compare planned item with object of type {0}".format(
                    item.__class__.__name__
                )
            )
        return self.time_period <= item.time_period

    def __gt__(self, item):
        """Check if self is over a greater period than other item.

        Args:
            item (PlannedItem): item to compare to.
        """
        if not isinstance(item, PlannedItem):
            raise PlannedItemError(
                "Cannot compare planned item with object of type {0}".format(
                    item.__class__.__name__
                )
            )
        return self.time_period > item.time_period

    def __ge__(self, item):
        """Check if self is over a greater or equal time period to other item.

        Args:
            item (PlannedItem): item to compare to.
        """
        if not isinstance(item, PlannedItem):
            raise PlannedItemError(
                "Cannot compare planned item with object of type {0}".format(
                    item.__class__.__name__
                )
            )
        return self.time_period >= item.time_period

    def get_item_container(self, calendar_period=None):
        """Get the list that this item should be contained in.

        Args:
            calendar_period (BaseCalendarPeriod or None): calendar period
                to query at. If None, use self.calendar_period.

        Returns:
            (list): list that planned item should be contained in.
        """
        calendar_period = fallback_value(
            calendar_period,
            self.calendar_period
        )
        return calendar_period.get_planned_items_container()

    def index(self):
        """Get index of item in its container.

        Returns:
            (int or None): index of item, if found.
        """
        container = self.get_item_container()
        if container is None:
            return None
        try:
            return container.index(self)
        except ValueError:
            return None

    def _get_task_to_update(self, new_tree_item=None, **kwargs):
        """Utility method to return the linked task item if it needs updating.

        This is used only by edit classes that update the task history based
        on updates to this planned item.

        Args:
            new_tree_item (BaseTaskItem or None): new linked tree item the
                planned item will have, if needed.
            **kwargs (dict): ignored, used for convenience so we can accept
                the same args for this and for the equivalent scheduled item
                method.

        Returns:
            (Task or None): linked tree item, if it's a task.
        """
        task_item = fallback_value(new_tree_item, self.tree_item)
        if not isinstance(task_item, Task):
            return None
        return task_item

    def _iter_influences(self):
        """Get tasks influenced at dates by this item.

        - currently this should yield either one influence at the end date of
            the item or no influence. However, in theory we could have items
            planned over time periods of longer than one day influencing on
            multiple days, so may need to update this method to reflect that.

        Yields:
            (Task): the influenced task.
            (Date): the date it's influenced at.
        """
        task = self._get_task_to_update()
        if task is not None:
            influencer_dict = task.history.get_influencer_dict(
                self.end_date,
                self,
            )
            if influencer_dict:
                yield (task, self.date)

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
            self._id = item_registry.generate_unique_id(
                "{0} ({1})".format(self.name, self.calendar_period.full_name)
            )
        return self._id

    @classmethod
    def from_dict(cls, dict_repr, calendar, calendar_period):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): root calendar object.
            calendar_period (BaseCalendarPeriod): the calendar period
                this is in.

        Returns:
            (PlannedItem): planned item.
        """
        planned_item = super(PlannedItem, cls).from_dict(
            dict_repr,
            calendar,
            calendar_period=calendar_period,
        )
        return planned_item

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = super(PlannedItem, self).to_dict()
        dict_repr[self.TIME_PERIOD_KEY] = self.time_period
        return dict_repr
