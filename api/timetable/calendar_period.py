"""Classes representing a time period of calendar data."""

from calendar import monthrange

from scheduler.api.common.date_time import Date, DateTime, TimeDelta
from scheduler.api.common.serializable import (
    NestedSerializable,
    SaveType,
    SerializableFileTypes
)
from .calendar_item import CalendarItem


class BaseCalendarPeriod(NestedSerializable):
    """Base class for all calendar period subclasses."""

    def __init__(self, calendar_obj, parent_obj):
        """Initialise class.

        Args:
            calendar_obj (Calendar): calendar root object, passed for
                convenience.
            parent_obj (BaseCalendarPeriod): calendar period parent object.
        """
        self._calendar = calendar_obj
        super(BaseCalendarPeriod, self).__init__(parent_obj)

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
    
    CALENDAR_ITEMS_KEY = "calendar_items"

    def __init__(self, calendar_obj, month_obj, date, scheduled_items=None):
        """Initialise calendar day object.

        Args:
            calendar_obj (Calendar): calendar root item, passed for
                convenience.
            month_obj (CalendarMonth): calendar month parent object.
            date (Date): date object.
            scheduled_items (list(CalendarItem) or None): scheduled items for
                that day, if any exist.
        """
        super(CalendarDay, self).__init__(calendar_obj, month_obj)
        self._date = date
        self._scheduled_items = scheduled_items or []

    @property
    def name(self):
        """Get name of day class, to use when saving.

        Args:
            name (str): name of class instance.
        """
        return self._date.string()

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
    def from_dict(cls, dict_repr, name, parent):
        """Initialise class from dict.

        The serialization stores each day file in a week directory. So the
        parent here is the week item, but the parent passed to the class
        __init__ is the month item.

        Args:
            dict_repr (dict): dictionary representing class.
            name (str): name of calendar day. This is the date string, used to
                key the calendar in the week dictionary.
            parent (CalendarWeek): calendar week parent item.

        Returns:
            (CalendarDay): calendar day object.
        """
        month_obj = parent.month
        date = Date.from_string(name)
        scheduled_items_list = dict_repr.get(cls.CALENDAR_ITEMS_KEY, [])
        calendar_day = cls(parent.calendar, month_obj, date)

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

    This means that the month-week-day class structure is a bit odd, since the
    CalendarMonth class stores a dict of days but converts into a dict of weeks
    in its to_dict method.
    Similarly the CalendarDay class has a reference to its corresponding month
    object, which it finds from its week object parent in the from_dict object.
    """
    _SAVE_TYPE = SaveType.DIRECTORY
    _MARKER_FILE = "week{0}".format(SerializableFileTypes.MARKER)
    _FILE_KEY = "days"
    _FILE_CLASS = CalendarDay
    DAYS_KEY = _FILE_KEY

    def __init__(
            self,
            calendar_obj,
            month_obj,
            start_date,
            length=7,
            days=None):
        """Initialise calendar week object.

        Args:
            calendar_obj (Calendar): calendar root item, passed for
                convenience.
            month_obj (CalendarMonth): calendar month parent item. This is the
                month corresponding to the starting date.
            start_date (date_time.Date): starting date of week. Note that this
                isn't necessarily a fixed day, as weeks in this framework can
                start from any day.
            length (int): length of week (in case we want to restrict it to
                less than 7 so it fits into a month, for the purpose of
                serialization or rows in a month view of a calendar).
            days (dict(CalendarDay) or None): dict of calendar day objects,
                if they already exist.
        """
        super(CalendarWeek, self).__init__(calendar_obj, month_obj)
        self._start_date = start_date
        self._length = length
        self._days = days or {}
        if not self._days:
            for i in range(length):
                date = start_date + TimeDelta(days=i)
                self._days[date] = CalendarDay(
                    calendar_obj,
                    month_obj,
                    date
                )

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

    # TODO: these from_dicts are all pretty messy (see how days are
    # initialised here in __init__ and then redone in from_dict) - should
    # fix a nicer way of doing this thatstill  allows parent to be passed
    @classmethod
    def from_dict(cls, dict_repr, name, parent):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            name (str): name of calendar week.
            parent (CalendarWeek): calendar month parent item.

        Returns:
            (CalendarMonth): calendar week object.
        """
        calendar_obj = parent.calendar
        month_obj = parent
        start_date_string, end_date_string = name.split("-")
        start_date = Date.from_string(start_date_string)
        end_date = Date.from_string(end_date_string)
        length = (start_date - end_date).get_num_days()
        class_instance = cls(calendar_obj, month_obj, start_date, length)

        days = {}
        for date_string, day_dict in dict_repr.get(cls.DAYS_KEY, {}).items():
            day = CalendarDay.from_dict(
                day_dict,
                date_string,
                class_instance
            )
            days[day.name] = day
        if days:
            class_instance._days = days
        return class_instance


class CalendarMonth(BaseCalendarPeriod):
    """Class representing a month of calendar data."""
    _SAVE_TYPE = SaveType.DIRECTORY
    _MARKER_FILE = "month{0}".format(SerializableFileTypes.MARKER)
    _SUBDIR_KEY = "weeks"
    _SUBDIR_CLASS = CalendarWeek
    WEEKS_KEY = _SUBDIR_KEY

    def __init__(self, calendar_obj, year_obj, month, days=None):
        """Initialise calendar month object.
        
        Args:
            calendar_obj (Calendar): calendar root item, passed for
                convenience.
            year_obj (CalendarYear): the calendar year parent item.
            month (int): the month number.
            days (list(CalendarDay) or None): list of calendar day
                objects, if they already exist.
        """
        super(CalendarMonth, self).__init__(calendar_obj, year_obj)
        self._month = month
        self._year = year_obj._year
        self._start_date = Date(self._year, self._month, 1)
        self._num_days = Date.month_range(self._month, self._year)
        self._end_date = self._start_date + TimeDelta(days=self._num_days-1)

        self._days = days or {}
        if not self._days:
            for i in range(self._num_days):
                date = self._start_date + TimeDelta(days=i)
                self._days[date] = CalendarDay(
                    calendar_obj,
                    self,
                    date
                )

    @property
    def name(self):
        """Get name of month class, to use in serialization.

        Args:
            name (str): name of class instance.
        """
        return Date.month_string_from_int(self._month, short=False)

    def to_dict(self):
        """Return dictionary representation of class.

        Currently this will always assume weeks start on a Monday.

        Returns:
            (dict): dictionary representation.
        """
        first_week_length = 7 - self._start_date.weekday
        last_week_length = self._end_date.weekday + 1
        first_week = CalendarWeek(
            self._calendar,
            self,
            self._start_date,
            first_week_length,
            
        )

        num_weeks = int(
            2 + (self._num_days - first_week_length - last_week_length) / 7
        )
        return_dict = {}
        return {
            self.WEEKS_KEY: {
            }
        }

    @classmethod
    def from_dict(cls, dict_repr, name, parent):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            name (str): name of calendar week.
            parent (CalendarWeek): calendar month parent item.

        Returns:
            (CalendarMonth): calendar week object.
        """
        calendar_obj = parent.calendar
        month_obj = parent
        start_date_string, end_date_string = name.split("-")
        start_date = Date.from_string(start_date_string)
        end_date = Date.from_string(end_date_string)
        length = (start_date - end_date).get_num_days()
        class_instance = cls(calendar_obj, month_obj, start_date, length)

        days = {}
        for date_string, day_dict in dict_repr.get(cls.DAYS_KEY, {}).items():
            day = CalendarDay.from_dict(
                day_dict,
                date_string,
                class_instance
            )
            days[day.name] = day
        if days:
            class_instance._days = days
        return class_instance


class CalendarYear(BaseCalendarPeriod):
    """Class representing a year of calendar data."""
    _SAVE_TYPE = SaveType.DIRECTORY
    _MARKER_FILE = "month{0}".format(SerializableFileTypes.MARKER)
    _SUBDIR_KEY = "months"
    _SUBDIR_CLASS = CalendarMonth

    def __init__(self, calendar_obj, year, months=None):
        """Initialise calendar year object.

        Args:
            calendar_obj (Calendar): the calendar parent item.
            year (int): the year number.
            months (list(CalendarMonth) or None): list of calendar month
                objects, if they already exist.
        """
        super(CalendarYear, self).__init__(calendar_obj, calendar_obj)
        self._year = year
        self._months = months or []
