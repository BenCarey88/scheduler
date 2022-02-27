"""Classes representing a time period of calendar data."""

from collections import OrderedDict

from scheduler.api.common.date_time import (
    Date,
    DateTimeError,
    TimeDelta
)
from scheduler.api.serialization.serializable import (
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
    the child classes are implemented as properties rather than filled during
    __init__ - this is to aid deserialization and ensure that all the calendar
    dicts have been filled before these relationships are created.
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

    def __init__(self, calendar, date, calendar_month=None):
        """Initialise calendar day object.

        Args:
            calendar (Calendar): calendar root item.
            date (Date): date object.
            calendar_month (CalendarMonth or None): calendar month object.

        Attrs:
            _scheduled_items (list(BaseCalendarItem)): all calendar item
                instances scheduled on this day.
        """
        super(CalendarDay, self).__init__(calendar)
        self._date = date
        self._calendar_month = calendar_month or self.calendar.get_month(
            date.year,
            date.month
        )
        self._scheduled_items = []

    @property
    def date(self):
        """Get date of day class.

        Returns:
            (Date): date of this day.
        """
        return self._date

    @property
    def name(self):
        """Get name of day class, to use in serialization.

        Args:
            name (str): name of class instance.
        """
        return self._date.string()

    @property
    def header_name(self):
        """Get name to use in headers for this day.

        Returns:
            (str): header name.
        """
        return "{0} {1}".format(
            self._date.weekday_string(),
            self._date.ordinal_string()
        )

    def iter_calendar_items(self):
        """Iterate through scheduled calendar items.

        This includes repeat instances as well.

        Yields:
            (CalendarItem): next calendar item.
        """
        for repeat_item in self.calendar._repeat_items:
            for item_instance in repeat_item.instances_at_date(self.date):
                yield item_instance
        for item in self._scheduled_items:
            yield item

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        if not self._scheduled_items:
            return {}
        return {
            self.CALENDAR_ITEMS_KEY: [
                item.to_dict() for item in self._scheduled_items
            ]
        }

    @classmethod
    def from_dict(cls, dict_repr, calendar, calendar_month, day_name):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): root calendar item.
            calendar_month (CalendarMonth): calendar month parent object.
            day_name (str): name of calendar day. This is the date string,
                used to key the calendar in the week dictionary.

        Returns:
            (CalendarDay or None): calendar day object, if can be initialized
                (ie. if it can be deserialized and belongs in calendar_month).
        """
        try:
            date = Date.from_string(day_name)
        except DateTimeError:
            return None
        if (date.month != calendar_month._month
                or date.year != calendar_month._year):
            return None
        calendar_day = cls(calendar, date, calendar_month)

        scheduled_items_list = dict_repr.get(cls.CALENDAR_ITEMS_KEY, [])
        scheduled_items = [
            CalendarItem.from_dict(scheduled_item_dict, calendar)
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
    _ORDER_FILE = "week{0}".format(SerializableFileTypes.ORDER)
    _MARKER_FILE = _ORDER_FILE
    _FILE_KEY = "days"
    _FILE_CLASS = CalendarDay
    _FILE_DICT_TYPE = OrderedDict

    DAYS_KEY = _FILE_KEY

    def __init__(
            self,
            calendar,
            start_date,
            length=Date.NUM_WEEKDAYS):
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
            self.__calendar_days = OrderedDict()
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

    # TODO: maybe replace with just week 1, week 2 etc. and sim. for day name?
    @property
    def name(self):
        """Get name of week class, to use in serialization.

        Args:
            name (str): name of class instance.
        """
        return "{0} to {1}".format(
            self.start_date.string(),
            self.end_date.string()
        )

    def iter_days(self):
        """Iterate through days in class.

        Yields:
            (CalendarDay): next calendar day.
        """
        for day in self._calendar_days.values():
            yield day

    def get_day_at_index(self, index):
        """Get day at given index from start of week.

        Args:
            index (int): index of day from start of week.
        """
        return list(self.iter_days())[index]

    def next_week(self):
        """Get calendar week starting immediately after this one.

        This returns a standard seven-day week, with starting day immediately
        after the end day of this one.

        Returns
            (CalendarWeek): the calendar week after this one.
        """
        return CalendarWeek(self.calendar, self.end_date + TimeDelta(days=1))

    def prev_week(self):
        """Get calendar week starting immediately before this one.

        This returns a standard seven-day week, with ending day immediately
        before the start day of this one.

        Returns
            (CalendarWeek): the calendar week before this one.
        """
        return CalendarWeek(
            self.calendar,
            self.start_date - TimeDelta(days=Date.NUM_WEEKDAYS)
        )

    def week_starting_next_day(self):
        """Get calendar week starting one day later than this one.

        Returns:
            (CalendarWeek): calendar week starting a day later than this one.
        """
        return CalendarWeek(
            self.calendar,
            self.start_date + TimeDelta(days=1)
        )

    def week_starting_prev_day(self):
        """Get calendar week starting one day earlier than this one.

        Returns:
            (CalendarWeek): calendar week starting a day earlier than this one.
        """
        return CalendarWeek(
            self.calendar,
            self.start_date - TimeDelta(days=1)
        )

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        days_dict = OrderedDict()
        for day in self._calendar_days.values():
            day_dict = day.to_dict()
            if day_dict:
                days_dict[day.name] = day_dict
        if days_dict:
            return {self.DAYS_KEY: days_dict}
        return {}

    @classmethod
    def from_dict(cls, dict_repr, calendar, calendar_month, week_name):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): calendar class.
            week_name (str): week string.
            calendar_month (CalendarMonth or None): calendar month of days
                in week (note that week that gets decoded from dict should
                always be within a month so we don't need to pass multiple
                months here.)

        Returns:
            (CalendarWeek or None): calendar week object, or None if can't
                be initialized.
        """
        try:
            start_date_string, end_date_string = week_name.split(" to ")
            start_date = Date.from_string(start_date_string)
            end_date = Date.from_string(end_date_string)
        except (DateTimeError, ValueError):
            return None
        length = (end_date - start_date).days + 1
        calendar_week = cls(calendar, start_date, length)

        weeks_dict = dict_repr.get(cls.DAYS_KEY, {})
        for day_name, day_dict in weeks_dict.items():
            calendar_day = CalendarDay.from_dict(
                day_dict,
                calendar,
                calendar_month,
                day_name,
            )
            if calendar_day:
                calendar._add_day(calendar_day)
        return calendar_week


class CalendarMonth(BaseCalendarPeriod):
    """Class representing a month of calendar data."""
    _SAVE_TYPE = SaveType.DIRECTORY
    _ORDER_FILE = "month{0}".format(SerializableFileTypes.ORDER)
    _MARKER_FILE = _ORDER_FILE
    _SUBDIR_KEY = "weeks"
    _SUBDIR_CLASS = CalendarWeek
    _SUBDIR_DICT_TYPE = OrderedDict

    WEEKS_KEY = _SUBDIR_KEY

    def __init__(self, calendar, year, month, calendar_year=None):
        """Initialise calendar month object.

        Args:
            calendar (Calendar): calendar root item.
            year (int): the year number.
            month (int): the month number.
            calendar_year (CalendarYear or None): calendar year object.
        """
        super(CalendarMonth, self).__init__(calendar)
        self._year = year
        self._month = month
        self._start_date = Date(year, month, 1)
        self._length = Date.num_days_in_month(year, month)
        self._end_date = self._start_date + TimeDelta(days=self._length-1)
        self._calendar_year = calendar_year or self.calendar.get_year(
            self._year
        )
        self.__calendar_days = None

    @property
    def _calendar_days(self):
        """Get days dictionary.

        Returns:
            (OrderedDict(Date, CalendarDay)): days in this week.
        """
        if not self.__calendar_days:
            self.__calendar_days = OrderedDict()
            for i in range(self._length):
                date = self._start_date + TimeDelta(days=i)
                day = self.calendar.get_day(date)
                self.__calendar_days[date] = day
        return self.__calendar_days

    @property
    def name(self):
        """Get name to use for month.

        Returns:
            (str): month name.
        """
        return Date.month_string_from_int(self._month, short=False)

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
                length = (starting_day - date.weekday) % Date.NUM_WEEKDAYS
            elif (self._end_date - date).days + 1 < Date.NUM_WEEKDAYS:
                # end of month, restrict length til end of month
                length = (self._end_date - date).days + 1
            week_list.append(CalendarWeek(self.calendar, date, length))
            date += TimeDelta(days=length)
        return week_list

    def iter_days(self):
        """Iterate through days in class.

        Yields:
            (CalendarDay): next calendar day.
        """
        for day in self._calendar_days.values():
            yield day
    
    def iter_weeks(self, starting_day=0):
        """Iterate through weeks in class.

        Args:
            starting_day (int or str): integer or string representing starting
                day for weeks. By default we start weeks on monday.

        Yields:
            (CalendarWeek): next calendar week.
        """
        for week in self.get_calendar_weeks(starting_day):
            yield week

    def to_dict(self):
        """Serialize class as dict.

        Returns:
            (dict): nested json dict representing calendar object and its
                contained calendar period objects.
        """
        weeks_dict = OrderedDict()
        for week in self.get_calendar_weeks():
            week_dict = week.to_dict()
            if week_dict:
                weeks_dict[week.name] = week_dict
        if weeks_dict:
            return {self.WEEKS_KEY: weeks_dict}
        return {}

    @classmethod
    def from_dict(cls, dict_repr, calendar, calendar_year, month_name):
        """Initialise calendar month from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): calendar class.
            calendar_year (CalendarYear): calendar year object.
            month_name (str): month string.

        Returns:
            (CalendarMonth or None): calendar year instance.
        """
        try:
            month = Date.month_int_from_string(month_name)
        except DateTimeError:
            return None
        calendar_month = cls(
            calendar,
            calendar_year._year,
            month,
            calendar_year
        )
        weeks_dict = dict_repr.get(cls.WEEKS_KEY, {})
        for week_name, week_dict in weeks_dict.items():
            # Note that we don't need to do anything with this, we're just
            # calling the week's from_dict method so it can add the days to
            # the calendar
            CalendarWeek.from_dict(
                week_dict,
                calendar,
                calendar_month,
                week_name
            )
        return calendar_month


class CalendarYear(BaseCalendarPeriod):
    """Class representing a year of calendar data."""
    _SAVE_TYPE = SaveType.DIRECTORY
    _ORDER_FILE = "year{0}".format(SerializableFileTypes.ORDER)
    _MARKER_FILE = _ORDER_FILE
    _SUBDIR_KEY = "months"
    _SUBDIR_CLASS = CalendarMonth
    _SUBDIR_DICT_TYPE = OrderedDict

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
            self.__calendar_months = OrderedDict()
            for i in range(self._length):
                month = self.calendar.get_month(self._year, i+1)
                self.__calendar_months[i+1] = month
        return self.__calendar_months

    @property
    def name(self):
        """Get name to use for year.

        Returns:
            (str): year name (just integer as string).
        """
        return str(self._year)

    def iter_months(self):
        """Iterate through months in class.

        Yields:
            (CalendarMonth): next calendar month.
        """
        for month in self._calendar_months.values():
            yield month

    def to_dict(self):
        """Serialize class as dict.

        Returns:
            (dict): nested json dict representing calendar year object and its
                contained calendar month objects.
        """
        months_dict = OrderedDict()
        for month in self._calendar_months.values():
            month_dict = month.to_dict()
            if month_dict:
                months_dict[month.name] = month_dict
        if months_dict:
            return {self.MONTHS_KEY: months_dict}
        return {}

    @classmethod
    def from_dict(cls, dict_repr, calendar, year_name):
        """Initialise calendar year class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar) calendar class.
            year_name (str): year string.

        Returns:
            (CalendarYear or None): calendar year instance.
        """
        try:
            year = int(year_name)
        except ValueError:
            return None
        calendar_year = cls(calendar, year)
        months_dict = dict_repr.get(cls.MONTHS_KEY, {})
        for month_name, month_dict in months_dict.items():
            calendar_month = CalendarMonth.from_dict(
                month_dict,
                calendar,
                calendar_year,
                month_name
            )
            if calendar_month:
                calendar._add_month(calendar_month)
        return calendar_year
