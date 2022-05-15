"""Planned item class."""

from scheduler.api.common.object_wrappers import (
    MutableAttribute,
    MutableHostedAttribute,
)
from scheduler.api.serialization import item_registry
from scheduler.api.serialization.serializable import (
    NestedSerializable,
    SaveType,
)


class PlannedItemSize(object):
    """Struct to store size types of item."""
    BIG = "big"
    MEDIUM = "medium"
    SMALL = "small"


class PlannedItemImportance(object):
    """Struct to store levels of importance for item."""
    CRITICAL = "critical"
    MODERATE = "moderate"
    MINOR = "minor"


class PlannedItem(NestedSerializable):
    """Class for items in planner tab."""
    _SAVE_TYPE = SaveType.NESTED

    TREE_ITEM_KEY = "tree_item"
    SIZE_KEY = "size"
    IMPORTANCE_KEY = "importance"
    CALENDAR_ITEMS_KEY = "calendar_items"

    def __init__(self, calendar, date, tree_item, size=None, importance=None):
        """Initialize class.

        Args:
            calendar (Calendar): calendar item.
            date (Date): date item is planned for.
            tree_item (BaseTreeItem): the task that this item represents.
            size (PlannedItemSize or None): size of item.
            importance (PlannedItemImportance or None): importance of item.
        """
        self._calendar = calendar
        self._date = MutableAttribute(date)
        self._tree_item = MutableHostedAttribute(tree_item)
        self._size = MutableAttribute(size)
        self._importance = MutableAttribute(importance)
        self._scheduled_items = []

    @property
    def calendar(self):
        """Get calendar object.

        Returns:
            (Calendar): the calendar object.
        """
        return self._calendar

    @property
    def date(self):
        """Get date item is planned for.

        Returns:
            (Date): date item is planned for.
        """
        return self._date.value

    @property
    def tree_item(self):
        """Get task this item is planning.

        Returns:
            (BaseTreeItem): task that this item is using.
        """
        return self._tree_item.value

    @property
    def name(self):
        """Get name of item.

        Returns:
            (str): name of item.
        """
        return self.tree_item.name

    @property
    def size(self):
        """Get size of item.

        Returns:
            (PlannedItemSize or None): size of item.
        """
        return self._size.value

    @property
    def importance(self):
        """Get importance of item.

        Returns:
            (PlannedItemImportance or None): importance of item.
        """
        return self._importance.value

    @property
    def scheduled_items(self):
        """Get scheduled items associated to this one.

        Returns:
            (list(BaseCalendarItem)): associated calendar items.
        """
        return [item.value for item in self._scheduled_items]

    def get_item_container(self, date=None):
        """Get the list that this item should be contained in.

        Args:
            date (Date or None): date to query at. If not given, use the
                item's internal date.

        Returns:
            (list): list that planned item should be contained in.
        """
        if date is None:
            date = self.date
        calendar_day = self._calendar.get_day(date)
        return calendar_day._planned_items

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
        tree_item = calendar.task_root.get_item_at_path(
            dict_repr.get(cls.TREE_ITEM_KEY)
        )
        size = dict_repr.get(cls.SIZE_KEY, None)
        importance = dict_repr.get(cls.IMPORTANCE_KEY, None)
        planned_item = cls(
            calendar,
            date,
            tree_item,
            size=size,
            importance=importance,
        )

        scheduled_item_ids = dict_repr.get(cls.CALENDAR_ITEMS_KEY, [])
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
        dict_repr = {self.TREE_ITEM_KEY: self.tree_item.path}
        if self._size:
            dict_repr[self.SIZE_KEY] = self.size
        if self._importance:
            dict_repr[self.IMPORTANCE_KEY] = self.importance
        if self._scheduled_items:
            dict_repr[self.CALENDAR_ITEMS_KEY] = [
                calendar_item.get_id()
                for calendar_item in self.scheduled_items
            ]
        return dict_repr
