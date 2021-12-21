"""Classes representing a time period of calendar data."""

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

    def __init__(self, scheduled_items=None):
        """Initialise calendar day object.
        
        Args:
            scheduled_items (list(CalendarItem) or None): scheduled items for
                that day, if any exist.
        """
        self._scheduled_items = scheduled_items or []

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
    def from_dict(cls, dict_repr):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.

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

    def __init__(self, calendar, days=None):
        """Initialise calendar week object.

        Args:
            calendar (Calendar): calendar object.
            days (list(CalendarDay) or None): list of calendar day objects,
                if they already exist.
        """
        self.calendar = calendar
        self._days = []

    def change_starting_day(self, date):
        """Change starting day to day from current start to given date."""

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """

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

    def __init__(self, days=None):
        """Initialise calendar month object.
        
        Args:
            days (list(CalendarDay) or None): list of calendar day
                objects, if they already exist.
        """
        self._days = days or []


class CalendarYear(Serializable):
    """Class representing a year of calendar data."""
    _SAVE_TYPE = SaveType.DIRECTORY
    _MARKER_FILE = "month{0}".format(SerializableFileTypes.MARKER)
    _SUBDIR_KEY = "months"
    _SUBDIR_CLASS = CalendarMonth

    def __init__(self, months=None):
        """Initialise calendar year object.

        Args:
            months (list(CalendarMonth) or None): list of calendar month
                objects, if they already exist.
        """
        self._months = months or []

