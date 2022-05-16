"""Planner object to store planned items."""

from functools import partial

from scheduler.api.serialization import item_registry
from scheduler.api.serialization.serializable import (
    NestedSerializable,
    SaveType,
)
from .calendar_period import (
    CalendarDay,
    CalendarMonth,
    CalendarWeek,
    CalendarYear,
)
from .planned_item import PlannedItem, PlannedItemTimePeriod


# TODO: switch to using directory serialization (work out structure
# and switchover plan)
class Planner(NestedSerializable):
    """Planner object."""
    _SAVE_TYPE = SaveType.FILE

    DAY_ITEMS_KEY = "day"
    WEEK_ITEMS_KEY = "week"
    MONTH_ITEMS_KEY = "month"
    YEAR_ITEMS_KEY = "year"
    ID_KEY = "__planned_item_id"

    def __init__(self, calendar):
        """Initialize class instance.

        Args:
            calendar (Calendar): calendar item.
        """
        self._calendar = calendar
        self._planned_day_items = {}
        self._planned_week_items = {}
        self._planned_month_items = {}
        self._planned_year_items = {}

    @property
    def calendar(self):
        """Get calendar object.

        Returns:
            (Calendar): the calendar object.
        """
        return self._calendar

    @property
    def task_root(self):
        """Get task root object.

        Returns:
            (TaskRoot): the task root object.
        """
        return self.calendar.task_root

    def get_planned_items_for_day(self, day):
        """Get planned items at given calendar day.

        Args:
            day (CalendarDay): day to query for.

        Returns:
            (list(PlannedItem)): items planned for that day.
        """
        return self._planned_day_items.get(day, [])

    def get_planned_items_for_week(self, week):
        """Get planned items at given calendar week.

        Note that since weeks are not fixed in the way that days, months
        and years are, the week list has to be handled separately. We
        cache values for each calendar week so we can store orders, but
        because this isn't guaranteed to be updated in the way that the day,
        month and year dicts are, we still need to get new planned items from
        each day, month and year.

        Note that this setup currently means that we lose any specific orders
        for weeks as soon as we swtich to the previous weekday, as the cached
        dict will be a completely different one.

        Args:
            week (CalendarWeek): week to query for.

        Returns:
            (list(PlannedItem)): items planned for that week.
        """
        planned_items = self._planned_week_items.get(week, [])
        for day in week.iter_days():
            for item in self.get_planned_items_for_day(day):
                if (item not in planned_items
                        and PlannedItemTimePeriod.WEEK in item.time_periods):
                    planned_items.append(item)
        for period in week.months + week.years:
            for item in self.get_planned_items_for_day(period):
                if (item not in planned_items
                        and item.is_planned_for_week(week)):
                    planned_items.append(item)
        self._planned_week_items[week] = planned_items
        return planned_items

    def get_planned_items_for_month(self, month):
        """Get planned items at given calendar month.

        Args:
            month (CalendarMonth): month to query for.

        Returns:
            (list(PlannedItem)): items planned for that month.
        """
        return self._planned_month_items.get(month)

    def get_planned_items_for_year(self, year):
        """Get planned items at given calendar year.

        Args:
            year (CalendarYear): year to query for.

        Yields:
            (list(PlannedItem)): items planned for that year.
        """
        return self._planned_year_items.get(year)

    def to_dict(self):
        """Serialize class as dict.

        To avoid repeated serialization of the same item, we serialize each
        item only in its highest level dict and just store references in
        the other dicts to use in the item registry.

        Returns:
            (dict): nested json dict representing planner object and its
                contained planned items.
        """
        dict_repr = {}
        already_serialized = []

        item_dicts_and_keys = [
            (self._planned_year_items, self.YEAR_ITEMS_KEY),
            (self._planned_month_items, self.MONTH_ITEMS_KEY),
            (self._planned_year_items, self.DAY_ITEMS_KEY),
            (self._planned_year_items, self.WEEK_ITEMS_KEY),
        ]
        for item_dict, key in item_dicts_and_keys:
            if not item_dict:
                continue
            serialized_items_dict = {}
            for period, item_list in item_dict.items():
                serialized_items_list = []
                for item in item_list:
                    # if we've already serialized the item, just add its id
                    if item in already_serialized:
                        serialized_items_list.append(
                            {self.ID_KEY: item.get_id()}
                        )
                    # otherwise, serialize it fully with its dictionary
                    else:
                        serialized_items_list.append(item.to_dict())
                        already_serialized.append(item)
                if serialized_items_list:
                    serialized_items_dict[period.name] = serialized_items_list
            dict_repr[key] = serialized_items_dict

        return dict_repr

    @classmethod
    def from_dict(cls, dict_repr, calendar):
        """Initialise planner class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): calendar object.

        Returns:
            (Planner): planner instance.
        """
        planner = cls(calendar)

        item_dicts_keys_and_periods = [
            (planner._planned_year_items, cls.YEAR_ITEMS_KEY, CalendarYear),
            (planner._planned_month_items, cls.MONTH_ITEMS_KEY, CalendarMonth),
            (planner._planned_week_items, cls.DAY_ITEMS_KEY, CalendarDay),
            (planner._planned_day_items, cls.WEEK_ITEMS_KEY, CalendarWeek),
        ]
        for item_dict, key, period_cls in item_dicts_keys_and_periods.items():
            ser_items_dict = dict_repr.get(key)
            if not ser_items_dict:
                continue
            for period_name, serialized_items_list in ser_items_dict.items():
                items_list = []
                period = period_cls.from_name(calendar, period_name)
                for dict_ in serialized_items_list:
                    # if item is only serialized by id, add it with a callback
                    if cls.ID_KEY in dict_.keys():
                        index = len(items_list)
                        items_list.append(None)
                        def callback(item):
                            items_list[index] = item
                        item_registry.register_callback(
                            dict_[cls.ID_KEY],
                            callback,
                        )
                    # otherwise add it directly
                    else:
                        items_list.append(
                            PlannedItem.from_dict(dict_, planner)
                        )
                item_dict[period] = items_list

        return planner
