"""Calendar class containing all calendar data."""

from collections import OrderedDict
from contextlib import contextmanager

from scheduler.api.common.date_time import Date, DateTime, Time, TimeDelta
from scheduler.api.serialization.serializable import (
    NestedSerializable,
    SaveType,
    SerializableFileTypes
)
from .calendar_period import (
    CalendarDay,
    CalendarMonth,
    CalendarWeek,
    CalendarYear
)
from .scheduled_item import RepeatScheduledItem
from .planned_item import PlannedItemTimePeriod


class CalendarError(Exception):
    """Exception for calendar-related errors."""


class Calendar(NestedSerializable):
    """Calendar object containing all calendar periods and items."""
    _SAVE_TYPE = SaveType.DIRECTORY
    _ORDER_FILE = "calendar{0}".format(SerializableFileTypes.ORDER)
    _INFO_FILE = "repeat_items{0}".format(SerializableFileTypes.INFO)
    _MARKER_FILE = _ORDER_FILE
    _SUBDIR_KEY = "years"
    _SUBDIR_CLASS = CalendarYear
    _SUBDIR_DICT_TYPE = OrderedDict

    YEARS_KEY = _SUBDIR_KEY
    REPEAT_ITEMS_KEY = "repeat_items"

    def __init__(self, task_root):
        """Initialise calendar class.

        Args:
            task_root (TaskRoot): root task item to use for scheduling and
                planning calendar items.
        """
        super(Calendar, self).__init__()
        self._task_root = task_root
        self._years = {}
        self._months = {}
        self._days = {}
        self._repeat_items = []

    @property
    def task_root(self):
        """Get task root object.

        Returns:
            (TaskRoot): the task root object.
        """
        return self._task_root

    def _add_day(self, calendar_day):
        """Add calendar day to calendar days dict.

        This should only be used during deserialization of the class from a
        dict. Otherwise we just fill these dicts with the setdefault methods
        above.

        Args:
            calendar_day (CalendarDay): calendar day object.

        Raises:
            (CalendarError): if the calendar_day already exists in the dict.
        """
        if self._days.get(calendar_day._date):
            raise CalendarError(
                "day {0} already exists in calendar".format(calendar_day.name)
            )
        self._days[calendar_day._date] = calendar_day

    def _add_month(self, calendar_month):
        """Add calendar month to calendar months dict.

        This should only be used during deserialization of the class from a
        dict. Otherwise we just fill these dicts with the setdefault methods
        above.

        Args:
            calendar_month (CalendarMonth): calendar month object.

        Raises:
            (CalendarError): if the calendar_month already exists in the dict.
        """
        if self._months.get((calendar_month._year, calendar_month._month)):
            raise CalendarError(
                "month {0} already exists in calendar".format(
                    calendar_month.name
                )
            )
        self._months[(calendar_month._year, calendar_month._month)] = (
            calendar_month
        )

    def _add_year(self, calendar_year):
        """Add calendar year to calendar year dict.

        This should only be used during deserialization of the class from a
        dict. Otherwise we just fill these dicts with the setdefault methods
        above.

        Args:
            calendar_year (CalendarMonth): calendar year object.

        Raises:
            (CalendarError): if the calendar_year already exists in the dict.
        """
        if self._years.get(calendar_year._year):
            raise CalendarError(
                "year {0} already exists in calendar".format(calendar_year.name)
            )
        self._years[calendar_year._year] = calendar_year

    def get_day(self, date):
        """Get calendar day data for given date.

        Args:
            date (Date): date to look for.

        Returns:
            (CalendarDay): calendar day object.
        """
        if not isinstance(date, Date):
            raise CalendarError(
                "Calendar get_day method requires date input, not {0}".format(
                    str(type(date))
                )
            )
        return self._days.setdefault(
            date,
            CalendarDay(self, date)
        )

    def get_month(self, year, month):
        """Get calendar month data for given year and month number.

        Args:
            year (int): year to search for.
            month (int): month to search for.

        Returns:
            (CalendarMonth): calendar month object.
        """
        if not isinstance(year, int) or not isinstance(month, int):
            raise CalendarError(
                "Calendar get_month method requires two int inputs, not "
                "({0}, {1})".format(str(type(year)), str(type(month)))
            )
        return self._months.setdefault(
            (year, month),
            CalendarMonth(self, year, month)
        )

    def get_year(self, year):
        """Get calendar year data for given year number.

        Args:
            year (int): year to search for.

        Returns:
            (CalendaryYear): calendar year object.
        """
        if not isinstance(year, int):
            raise CalendarError(
                "Calendar get_year method requires int input, not {0}".format(
                    str(type(year))
                )
            )
        return self._years.setdefault(
            year,
            CalendarYear(self, year)
        )

    def get_week_containing_date(self, date, starting_day=0, length=7):
        """Get week containing given date.

        Args:
            date (Date): date to get week for.
            starting_day (int or str): integer or string representing starting
                day for weeks. By default we start weeks on monday.
            length (int): length of week.

        Returns:
            (CalendarWeek): calendar week objects that contains given date.
        """
        if isinstance(starting_day, str):
            starting_day = Date.weekday_int_from_string(starting_day)
        days_offset = (date.weekday - starting_day) % 7
        starting_date = date - TimeDelta(days=days_offset)
        return CalendarWeek(self, starting_date, length=length)

    def get_week_starting_with_date(self, date, length=7):
        """Get week that starts with given date.

        Args:
            date (Date): date to get week for.
            length (int): length of week.

        Returns:
            (CalendarWeek): calendar week objects that contains given date.
        """
        return self.get_week_containing_date(date, date.weekday, length=length)

    def get_current_week(self, starting_day=0, length=7):
        """Get current calendar week.

        Args:
            starting_day (int or str): integer or string representing starting
                day for weeks. By default we start weeks on monday.
            length (int): length of week.

        Returns:
            (CalendarWeek): calendar week object that contains current date.
        """
        return self.get_week_containing_date(
            Date.now(),
            starting_day,
            length=length,
        )

    def get_current_period(self, period_type, weekday_start=0, week_length=7):
        """Get current calendar period of given type.

        Args:
            period_type (class or PlannedItemTimePeirod): calendar period to
                check for. For convenience, we can also use planned item
                time period types.
            weekday_start (int or str): integer or string representing starting
                day for weeks. By default we start weeks on monday.
            length (int): length of week.

        Returns:
            (CalendarPeriod): calendar period object that contains current
                date.
        """
        date = Date.now()
        period_type = {
            PlannedItemTimePeriod.DAY: CalendarDay,
            PlannedItemTimePeriod.WEEK: CalendarWeek,
            PlannedItemTimePeriod.MONTH: CalendarMonth,
            PlannedItemTimePeriod.YEAR: CalendarYear,
        }.get(period_type, period_type)
        if period_type == CalendarDay:
            return self.get_day(date)
        if period_type == CalendarWeek:
            return self.get_current_week(weekday_start, week_length)
        if period_type == CalendarMonth:
            return self.get_month(date.year, date.month)
        if period_type == CalendarYear:
            return self.get_year(date.year)
        raise TypeError(
            "Cannot find calendar period for period of type {0}".format(
                str(period_type)
            )
        )

    # @contextmanager
    # def filter_items(self, filters):
    #     """Contextmanager to filter _items list temporarily.

    #     This uses the filters defined in the filters module.

    #     Args:
    #         filters (list(BaseFilter)): types of filtering required.
    #     """
    #     _items = self._items
    #     try:
    #         for filter in filters:
    #             self._items = filter.filter_function(self._items)
    #         yield
    #     finally:
    #         self._items = _items

    def to_dict(self):
        """Serialize class as dict.

        Note that we only serialize the year objects here and leave the
        subclasses to do the remaining serialization.

        Returns:
            (dict): nested json dict representing calendar object and its
                contained calendar period objects.
        """
        dict_repr = {}
        repeat_items_list = []
        for item in self._repeat_items:
            repeat_item_dict = item.to_dict()
            if repeat_item_dict:
                repeat_items_list.append(repeat_item_dict)
        if repeat_items_list:
            dict_repr[self.REPEAT_ITEMS_KEY] = repeat_items_list

        years_dict = OrderedDict()
        years = sorted(self._years.keys())
        for year in years:
            calendar_year = self.get_year(year)
            year_dict = calendar_year.to_dict()
            if year_dict:
                years_dict[calendar_year.name] = year_dict
        if years_dict:
            dict_repr[self.YEARS_KEY] = years_dict

        return dict_repr

    @classmethod
    def from_dict(cls, dict_repr, task_root):
        """Initialise calendar class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            task_root (TaskRoot): task root object.

        Returns:
            (Calendar): calendar instance.
        """
        calendar = cls(task_root)
        years_dict = dict_repr.get(cls.YEARS_KEY, {})
        for year_name, year_dict in years_dict.items():
            calendar._add_year(
                CalendarYear.from_dict(year_dict, calendar, year_name)
            )
        repeat_items_list = dict_repr.get(cls.REPEAT_ITEMS_KEY, [])
        for repeat_item_dict in repeat_items_list:
            calendar._repeat_items.append(
                RepeatScheduledItem.from_dict(repeat_item_dict, calendar)
            )
        return calendar
