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


class PlannedItemTimePeriod(object):
    """Struct to store potential time periods to plan over."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


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

    START_DATE_KEY = "start_date"
    END_DATE_KEY = "end_date"
    TREE_ITEM_KEY = "tree_item"
    TIME_PERIODS_KEY = "time_periods"
    SIZE_KEY = "size"
    IMPORTANCE_KEY = "importance"
    CALENDAR_ITEMS_KEY = "calendar_items"
    ID_KEY = "id"

    def __init__(
            self,
            planner,
            start_date,
            end_date,
            tree_item,
            time_periods=None,
            size=None,
            importance=None):
        """Initialize class.

        Args:
            calendar (Calendar): calendar item.
            start_date (Date): start date item is planned for.
            end_date (Date): end date item is planned for.
            tree_item (BaseTreeItem): the task that this item represents.
            time_periods (list(PlannedItemTimePeriod) or None): time periods
                this planned item should be included in.
            size (PlannedItemSize or None): size of item.
            importance (PlannedItemImportance or None): importance of item.
        """
        self._planner = planner
        self._start_date = MutableAttribute(start_date)
        self._end_date = MutableAttribute(end_date)
        self._tree_item = MutableHostedAttribute(tree_item)
        self._size = MutableAttribute(size)
        self._importance = MutableAttribute(importance)
        self._time_periods = time_periods or []
        self._scheduled_items = []

    @property
    def planner(self):
        """Get planner object.

        Returns:
            (Planner): the planner object.
        """
        return self._planner

    @property
    def calendar(self):
        """Get calendar object.

        Returns:
            (Calendar): the calendar object.
        """
        return self._planner.calendar

    @property
    def start_date(self):
        """Get start date item is planned for.

        Returns:
            (Date): start date item is planned for.
        """
        return self._start_date.value

    @property
    def end_date(self):
        """Get end date item is planned for.

        Returns:
            (Date): end date item is planned for.
        """
        return self._start_date.value

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
    def time_periods(self):
        """Get time periods this is planned for.

        Returns:
            (list(PlannedItemTimePeriod)): time periods.
        """
        return self._time_periods

    @property
    def scheduled_items(self):
        """Get scheduled items associated to this one.

        Returns:
            (list(BaseCalendarItem)): associated calendar items.
        """
        return [item.value for item in self._scheduled_items]

    def is_planned_for_day(self, day):
        """Check if this is planned for given day.

        Args:
            day (CalendarDay): calendar day to check.

        Returns:
            (bool): whether or not planned for given day.
        """
        return (
            PlannedItemTimePeriod.DAY in self.time_periods
            and (self.start_date <= day.date <= self.end_date)
        )

    def is_planned_for_week(self, week):
        """Check if this is planned for given week.

        Args:
            week (CalendarWeek): calendar week to check.

        Returns:
            (bool): whether or not planned for given week.
        """
        if PlannedItemTimePeriod.WEEK not in self.time_periods:
            return False
        if week.contains(self.start_date) or week.contains(self.end_date):
            return True
        if self.start_date <= week.start_date <= self.end_date:
            return True
        return False

    def is_planned_for_month(self, month):
        """Check if this is planned for given month.

        Args:
            month (CalendarMonth): calendar month to check.

        Returns:
            (bool): whether or not planned for given month.
        """
        if PlannedItemTimePeriod.MONTH not in self.time_periods:
            return False
        if month.contains(self.start_date) or month.contains(self.end_date):
            return True
        if self.start_date <= month.start_day.date <= self.end_date:
            return True
        return False

    def is_planned_for_year(self, year):
        """Check if this is planned for given year.

        Args:
            year (CalendarYear): calendar year to check.

        Returns:
            (bool): whether or not planned for given year.
        """
        if PlannedItemTimePeriod.YEAR not in self.time_periods:
            return False
        if year.contains(self.start_date) or year.contains(self.end_date):
            return True
        if self.start_date <= year.start_day.date <= self.end_date:
            return True
        return False

    def get_item_containers(self):
        """Get the dicts that this item should be contained in.

        Returns:
            (list(dict)): list that planned item should be contained in.
        """
        containers = []
        if PlannedItemTimePeriod.DAY in self._time_periods:
            containers.append(self.planner._planned_day_items)
        return self.planner._planned_items

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

    def get_id(self):
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
            self._id = item_registry.generate_unique_id(self.name)
        return self._id

    @classmethod
    def from_dict(cls, dict_repr, planner):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            planner (Planner): root planner object.

        Returns:
            (PlannedItem): planned item.
        """
        start_date = dict_repr.get(cls.START_DATE_KEY)
        end_date = dict_repr.get(cls.END_DATE_KEY)
        tree_item = planner.task_root.get_item_at_path(
            dict_repr.get(cls.TREE_ITEM_KEY)
        )
        time_periods = dict_repr.get(cls.TIME_PERIODS_KEY, None)
        size = dict_repr.get(cls.SIZE_KEY, None)
        importance = dict_repr.get(cls.IMPORTANCE_KEY, None)
        planned_item = cls(
            planner,
            start_date,
            end_date,
            tree_item,
            time_periods,
            size=size,
            importance=importance,
        )

        scheduled_item_ids = dict_repr.get(cls.CALENDAR_ITEMS_KEY, [])
        for id in scheduled_item_ids:
            item_registry.register_callback(
                id,
                planned_item._add_scheduled_item
            )
        planned_item_id = dict_repr.get(cls.ID_KEY, None)
        if planned_item_id is not None:
            item_registry.register_item(planned_item_id, planned_item)
        return planned_item

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = {
            self.START_DATE_KEY: self.start_date,
            self.END_DATE_KEY: self.end_date,
            self.TREE_ITEM_KEY: self.tree_item.path,
        }
        if self._time_periods:
            dict_repr[self.TIME_PERIODS_KEY] = self._time_periods
        if self._size:
            dict_repr[self.SIZE_KEY] = self.size
        if self._importance:
            dict_repr[self.IMPORTANCE_KEY] = self.importance
        if self._scheduled_items:
            dict_repr[self.CALENDAR_ITEMS_KEY] = [
                calendar_item.get_id()
                for calendar_item in self.scheduled_items
            ]
        dict_repr[self.ID_KEY] = self.get_id()
        return dict_repr
