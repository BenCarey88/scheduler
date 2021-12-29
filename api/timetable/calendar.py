"""Calendar class containing all calendar data."""

from contextlib import contextmanager

from scheduler.api.common.date_time import Date, DateTime
from scheduler.api.common.serializable import (
    NestedSerializable,
    SaveType,
    SerializableFileTypes
)
from .calendar_period import CalendarDay, CalendarMonth, CalendarYear


class CalendarError(Exception):
    """Exception for calendar-related errors."""


class Calendar(NestedSerializable):
    """Calendar object containing all calendar items."""
    _SAVE_TYPE = SaveType.DIRECTORY
    _MARKER_FILE = "calendar{0}".format(SerializableFileTypes.MARKER)
    _SUBDIR_KEY = "years"
    _SUBDIR_CLASS = CalendarYear
    YEARS_KEY = _SUBDIR_KEY

    def __init__(self, task_root):
        """Initialise calendar class.

        Args:
            task_root (TaskRoot): root task item to use for scheduling task
                calendar items.
        """
        self.task_root = task_root
        self._years = {}
        self._months = {}
        self._days = {}

    def get_day(self, date):
        """Get calendar day data for given date.

        Args:
            date (Date): date to look for.

        Returns:
            (CalendarDay): calendar day object.
        """
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
        return self._months.setdefault(
            year,
            CalendarYear(self, year)
        )

    def _add_day(self, calendar_day):
        """Add calendar day to calendar days dict.

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

        Args:
            calendar_year (CalendarMonth): calendar year object.

        Raises:
            (CalendarError): if the calendar_year already exists in the dict.
        """
        if self._years.get(calendar_year._year):
            raise CalendarError(
                "year {0} already exists in calendar".format(calendar_year.name)
            )
        self._days[calendar_year._year] = calendar_year

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

        Note that there is a large amount of redundancy in the attributes
        stored by the various calendar classes to allow easy access of things.
        Hence we only serialize the year objects here and leave the subclasses
        to do the remaining serialization.

        Returns:
            (dict): nested json dict representing calendar object and its
                contained calendar period objects.
        """
        return {
            self.YEARS_KEY: {
                year.name: year.to_dict()
                for year in self._years.values()
            }
        }

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
        return calendar
