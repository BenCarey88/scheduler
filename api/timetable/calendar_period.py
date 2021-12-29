"""Classes representing a time period of calendar data."""

import json
from scheduler.api.common.date_time import (
    BaseDateTimeWrapper,
    Date,
    DateTime,
    TimeDelta
)
from scheduler.api.common.serializable import (
    NestedSerializable,
    SaveType,
    SerializableFileTypes
)
from .calendar_item import CalendarItem


class BaseCalendarPeriod(NestedSerializable):
    """Base class for all calendar period subclasses.

    The calendar class stores dicts of each year, month and day object. These
    classes are effectively just containers to allow easy access and traversal
    of various blocks of calendar data.

    These store attributes to a parent class and a dict of child classes, but
    these are implemented rather than filled during __init__ - this is to aid
    deserialization and ensure that all the calendar dicts have been filled
    before these relationships are created.
    """
    def __init__(self, calendar):
        """Initialise class.

        Args:
            calendar (Calendar): calendar root object.
        """
        self._calendar = calendar

    @property
    def calendar(self):
        """Get root calendar object.

        Returns:
            (Calendar): calendar root object.
        """
        return self._calendar


class CalendarDay(BaseCalendarPeriod):
    """Class representing a day of calendar data."""
    _SAVE_TYPE = SaveType.FILE
    _KEY_TYPE = Date
    CALENDAR_ITEMS_KEY = "calendar_items"

    def __init__(self, calendar, date):
        """Initialise calendar day object.

        Args:
            calendar (Calendar): calendar root item.
            date (Date): date object.
        """
        super(CalendarDay, self).__init__(calendar)
        self._date = date
        self._scheduled_items = []
        self.__calendar_month = None

    @property
    def _calendar_month(self):
        """Get calendar month object of this day.

        Returns:
            (CalendarMonth): calendar month object.
        """
        if not self.__calendar_month:
            self.__calendar_month = self.calendar.get_month(
                self._date.year,
                self._date.month
            )
        return self.__calendar_month

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        return {
            self.CALENDAR_ITEMS_KEY: [
                item.to_dict() for item in self._scheduled_items
            ]
        }

    @classmethod
    def from_dict(cls, dict_repr, calendar, day_name):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): root calendar item.
            day_name (str): name of calendar day. This is the date string,
                used to key the calendar in the week dictionary.

        Returns:
            (CalendarDay): calendar day object.
        """
        date = Date.from_string(day_name)
        calendar_day = cls(date, calendar)

        scheduled_items_list = dict_repr.get(cls.CALENDAR_ITEMS_KEY, [])
        scheduled_items = [
            CalendarItem.from_dict(scheduled_item_dict, parent=calendar_day)
            for scheduled_item_dict in scheduled_items_list
        ]
        calendar_day._scheduled_items = scheduled_items
        return calendar_day


class CalendarWeek(BaseCalendarPeriod):
    """Class representing a week of calendar data.

    Note that unlike the other classes in this module, this one is not fixed -
    it gets generated on the fly when needed to be viewed, and the starting
    day may be changed.
    """
    _SAVE_TYPE = SaveType.DIRECTORY
    _MARKER_FILE = "week{0}".format(SerializableFileTypes.MARKER)
    _FILE_KEY = "days"
    _FILE_CLASS = CalendarDay
    DAYS_KEY = _FILE_KEY

    def __init__(self, calendar, start_date, length=Date.NUM_WEEKDAYS):
        """Initialise calendar week object.

        Args:
            calendar (Calendar): calendar root item.
            start_date (date_time.Date): starting date of week. Note that this
                isn't necessarily a fixed day, as weeks in this framework can
                start from any day.
            length (int): length of week (in case we want to restrict it to
                less than 7 so it fits into a month, for the purpose of
                serialization or rows in a month view of a calendar).
        """
        super(CalendarWeek, self).__init__(calendar)
        self._start_date = start_date
        self._length = length
        self.__calendar_days = None

    @property
    def _calendar_days(self):
        """Get days dictionary.

        Returns:
            (dict(Date, CalendarDay)): days in this week.
        """
        if not self.__calendar_days:
            self.__calendar_days = {}
            for i in range(self._length):
                date = self._start_date + TimeDelta(days=i)
                day = self.calendar.get_day(date)
                self.__calendar_days[date] = day
        return self.__calendar_days

    @property
    def start_date(self):
        """Get start date of week.

        Returns:
            (Date): start date.
        """
        return self._start_date

    @property
    def end_date(self):
        """Get end date of week.

        Returns:
            (Date): end date.
        """
        return self._start_date + TimeDelta(days=self._length-1)

    @property
    def name(self):
        """Get name of week class, to use in serialization.

        Args:
            name (str): name of class instance.
        """
        return "{0}-{1}".format(
            self.start_date.string(),
            self.end_date.string()
        )

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        return {
            self.DAYS_KEY: {
                day.name: day.to_dict()
                for day in self._days.values()
            }
        }

    @classmethod
    def from_dict(cls, dict_repr, calendar, week_name):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): calendar class.
            week_name (str): week string.

        Returns:
            (CalendarWeek): calendar week object.
        """
        start_date_string, end_date_string = week_name.split("-")
        start_date = Date.from_string(start_date_string)
        end_date = Date.from_string(end_date_string)
        length = (end_date - start_date).days + 1
        calendar_week = cls(calendar, start_date, length)

        weeks_dict = dict_repr.get(cls.DAYS_KEY, {})
        for day_name, day_dict in weeks_dict.items():
            calendar._add_day(
                CalendarDay.from_dict(day_dict, calendar, day_name)
            )
        return calendar_week


class CalendarMonth(BaseCalendarPeriod):
    """Class representing a month of calendar data."""
    _SAVE_TYPE = SaveType.DIRECTORY
    _MARKER_FILE = "month{0}".format(SerializableFileTypes.MARKER)
    _SUBDIR_KEY = "weeks"
    _SUBDIR_CLASS = CalendarWeek
    WEEKS_KEY = _SUBDIR_KEY

    def __init__(self, calendar, year, month):
        """Initialise calendar month object.

        Args:
            calendar (Calendar): calendar root item.
            year (int): the year number.
            month (int): the month number.
        """
        super(CalendarMonth, self).__init__(calendar)
        self._year = year
        self._month = month
        self._start_date = Date(self._year, self._month, 1)
        self._length = Date.month_range(self._month, self._year)
        self._end_date = self._start_date + TimeDelta(days=self._length-1)
        self.__calendar_days = None
        self.__calendar_year = None

    @property
    def _calendar_days(self):
        """Get days dictionary.

        Returns:
            (dict(Date, CalendarDay)): days in this week.
        """
        if not self.__calendar_days:
            self.__calendar_days = {}
            for i in range(self._length):
                date = self._start_date + TimeDelta(days=i)
                day = self.calendar.get_day(date)
                self.__calendar_days[date] = day
        return self.__calendar_days

    @property
    def _calendar_year(self):
        """Get calendar year object for this month.

        Returns:
            (CalendarYear): calendar year object.
        """
        if not self.__calendar_year:
            self.__calendar_year = self.calendar.get_year(self._date.year)
        return self.__calendar_year

    def get_calendar_weeks(self, starting_day=0):
        """Get calendar weeks list.

        Args:
            starting_day (int or str): integer or string representing starting
                day for weeks. By default we start weeks on monday.

        Returns:
            (list(CalendarWeek)): list of calendar week objects for this month.
        """
        week_list = []
        if isinstance(starting_day, str):
            starting_day = Date.weekday_int_from_string(starting_day)
        date = self._start_date
        while date <= self._end_date:
            length = Date.NUM_WEEKDAYS
            if date.weekday != starting_day:
                # beginning of month, restrict length til next start day
                length = (starting_day - date.weekday) % Date.NUM_WEEKDAYS + 1
            elif (self._end_date - date).days + 1 < Date.NUM_WEEKDAYS:
                # end of month, restrict length til end of month
                length = (self._end_date - date).days + 1
            week_list.append(CalendarWeek(self.calendar, date, length))
            date += TimeDelta(days=length)
        return week_list

    @property
    def name(self):
        """Get name to use for month.

        Returns:
            (str): month name.
        """
        return Date.month_string_from_int(self._month, short=False)

    def to_dict(self):
        """Serialize class as dict.

        Returns:
            (dict): nested json dict representing calendar object and its
                contained calendar period objects.
        """
        return {
            self.WEEKS_KEY: {
                week.name: week.to_dict()
                for week in self.get_calendar_weeks().values()
            }
        }

    @classmethod
    def from_dict(cls, dict_repr, calendar, year, month_name):
        """Initialise calendar month from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): calendar class.
            year (int): year number
            month_name (str): month string.

        Returns:
            (CalendarMonth): calendar year instance.
        """
        month = Date.month_int_from_string(month_name)
        calendar_month = cls(calendar, month)
        weeks_dict = dict_repr.get(cls.WEEKS_KEY, {})
        for week_name, week_dict in weeks_dict.items():
            # Note that we don't need to do anything with this, we're just
            # calling the week's from dict method so it can add the days to
            # the calendar
            CalendarWeek.from_dict(week_dict, calendar, week_name)
        return calendar_month


class CalendarYear(BaseCalendarPeriod):
    """Class representing a year of calendar data."""
    _SAVE_TYPE = SaveType.DIRECTORY
    _MARKER_FILE = "month{0}".format(SerializableFileTypes.MARKER)
    _SUBDIR_KEY = "months"
    _SUBDIR_CLASS = CalendarMonth
    MONTHS_KEY = _SUBDIR_KEY

    def __init__(self, calendar, year):
        """Initialise calendar year object.

        Args:
            calendar_obj (Calendar): the calendar parent item.
            year (int): the year number.
        """
        super(CalendarYear, self).__init__(calendar)
        self._year = year
        self._length = Date.NUM_MONTHS
        self.__calendar_months = None

    @property
    def _calendar_months(self):
        """Get months dictionary.

        Returns:
            (dict(int, CalendarDay)): months in this year.
        """
        if not self.__calendar_months:
            self.__calendar_months = {}
            for i in range(self._length):
                month = self.calendar.get_month(self._year, i)
                self.__calendar_months[i] = month
        return self.__calendar_months

    @property
    def name(self):
        """Get name to use for year.

        Returns:
            (str): year name (just integer as string).
        """
        return str(self._year)

    def to_dict(self):
        """Serialize class as dict.

        Returns:
            (dict): nested json dict representing calendar year object and its
                contained calendar month objects.
        """
        return {
            self.MONTHS_KEY: {
                month.name: month.to_dict()
                for month in self._calendar_months.values()
            }
        }

    @classmethod
    def from_dict(cls, dict_repr, calendar, year_name):
        """Initialise calendar year class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar) calendar class.
            year_name (str): year string.

        Returns:
            (CalendarYear): calendar year instance.
        """
        year = int(year_name)
        calendar_year = cls(calendar, year)
        months_dict = dict_repr.get(cls.MONTHS_KEY, {})
        for month_name, month_dict in months_dict.items():
            calendar._add_month(
                CalendarMonth.from_dict(month_dict, calendar, year, month_name)
            )
        return calendar_year
