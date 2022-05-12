"""Planned item class."""

from collections import OrderedDict

from scheduler.api.common.date_time import (
    Date,
    DateTime,
    DateTimeError,
    Time,
    TimeDelta,
)
from scheduler.api.common.object_wrappers import (
    MutableAttribute,
    MutableHostedAttribute,
)
from scheduler.api.serialization import item_registry
from scheduler.api.serialization.serializable import (
    NestedSerializable,
    SaveType,
)


class PlannedItem(NestedSerializable):
    """Class for items in planner tab."""
    _SAVE_TYPE = SaveType.NESTED

    CALENDAR_ITEMS_KEY = "calendar_items"

    def __init__(self, calendar, date, scheduled_items=None):
        """Initialize class.

        Args:
            calendar (Calendar): calendar item.
            date (Date): date item is scheduled for.
            scheduled_items (list(BaseCalendarItem or None)): list of scheduled
                scheduled calendar items corresponding to this planned item.
        """
        self._calendar = calendar
        self._date = MutableAttribute(date)
        self._scheduled_items = [
            MutableHostedAttribute(item) for item in scheduled_items or []
        ]

    @property
    def calendar(self):
        """Get calendar object.

        Returns:
            (Calendar): the calendar object.
        """
        return self._calendar

    @property
    def date(self):
        """Get date item is planned for"""
        return self._date.value

    @property
    def scheduled_items(self):
        """Get scheduled items associated to this one.

        Returns:
            (list(BaseCalendarItem)): associated calendar items.
        """
        return [item.value for item in self._scheduled_items]

    def _add_scheduled_item(self, scheduled_item):
        """Add scheduled item (to be used during deserialization).

        Args:
            scheduled_item (BaseCalendarItem): calendar item to associate
                to this planned item.
        """
        if scheduled_item not in self.scheduled_items:
            self._scheduled_items.append(
                MutableHostedAttribute(scheduled_item)
            )

    @classmethod
    def from_dict(cls, dict_repr, calendar, date):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): root calendar object.
            date (Date): date of item.

        Returns:
            (PlannedItem): planned item.
        """
        scheduled_item_ids = [
            dict_repr.get(cls.CALENDAR_ITEMS_KEY, [])
        ]
        planned_item = cls(calendar, date)
        for id in scheduled_item_ids:
            item_registry.register_callback(
                id,
                planned_item._add_scheduled_item
            )
        return planned_item

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = {}
        if self._scheduled_items:
            dict_repr[self.CALENDAR_ITEMS_KEY] = [
                calendar_item.get_id()
                for calendar_item in self.scheduled_items
            ]
        return dict_repr
