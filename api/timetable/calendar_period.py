"""Classes representing a time period of calendar data."""

from typing import OrderedDict
from scheduler.api.common.date_time import DateTime
from scheduler.api.common.serializable import (
    SaveType,
    Serializable,
    SerializableFileTypes
)


class CalendarDay(Serializable):
    """Class representing a day of calendar data."""
    _SAVE_TYPE = SaveType.FILE
    
    CALENDAR_ITEMS_KEY = "calendar_items"

    def __init__(self, month_obj, date, scheduled_items=None):
        """Initialise calendar day object.

        Args:
            date (Date): date object.
            scheduled_items (list(CalendarItem) or None): scheduled items for
                that day, if any exist.
        """
        super(CalendarDay, self).__init__(month_obj)
        self._date = date
        self._scheduled_items = scheduled_items or []

    @property
    def name(self):
        """Get name of day class, to use when saving.

        Args:
            name (str): name of class instance.
        """
        return self._date.title_string()

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

        Args:
            dict_repr (dict): dictionary representing class.
            name (str): name of calendar day.
            parent (CalendarWeek): calendar week parent item.

        Returns:
            (CalendarDay): calendar item object.
        """
        scheduled_items = dict_repr.get(cls.CALENDAR_ITEMS_KEY)
        return cls(scheduled_items)


# QUESTION: how do we ensure only some of the week gets written?
class CalendarWeek(Serializable):
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

    def __init__(self, month_obj, start_date, length=7, days=None):
        """Initialise calendar week object.

        Args:
            month_obj (CalendarMonth): calendar month parent item.
            days (list(CalendarDay) or None): list of calendar day objects,
                if they already exist.
            start_date (date_time.Date): starting date of week.
            length (int): length of week (in case we want to restrict it to
                fit into a month). Defaults to 7.
        """
        super(CalendarWeek, self).__init__(month_obj)
        self._start_date = start_date
        self._length = length
        self._days = days or []

    @property
    def name(self):
        """Get name of week class, to use when saving.

        Args:
            name (str): name of class instance.
        """
        return self._date.title_string()

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        return {
            self.DAYS_KEY: {
                day.name : day.to_dict() for day in self._days
            }
        }

    @classmethod
    def from_dict(cls, dict_repr):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.

        Returns:
            (CalendarDay or None): calendar item, or None if can't be
                initialised.
        """


class CalendarMonth(Serializable):
    """Class representing a month of calendar data."""
    _SAVE_TYPE = SaveType.DIRECTORY
    _MARKER_FILE = "month{0}".format(SerializableFileTypes.MARKER)
    _SUBDIR_KEY = "weeks"
    _SUBDIR_CLASS = CalendarWeek

    def __init__(self, year_obj, month, days=None):
        """Initialise calendar month object.
        
        Args:
            year_obj (CalendarYear): the calendar year parent item.
            month (int): the month number.
            days (list(CalendarDay) or None): list of calendar day
                objects, if they already exist.
        """
        super(CalendarMonth, self).__init__(year_obj)
        self._month = month
        self._days = days or []


class CalendarYear(Serializable):
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
        super(CalendarYear, self).__init__(calendar_obj)
        self._year = year
        self._months = months or []
