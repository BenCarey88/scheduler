"""Classes representing a time period of calendar data."""

from scheduler.api.common.date_time import DateTime


class CalendarYear(object):
    """Class representing a year of calendar data."""


class CalendarMonth(object):
    """Class representing a month of calendar data."""
    def __init__(self):
        self._days = []


class CalendarWeek(object):
    """Class representing a week of calendar data.

    Note that unlike the other classes in this module, this one is not fixed -
    it gets generated on the fly when needed to be viewed, as the starting
    day may be changed.
    """
    def __init__(self, calendar):
        self.calendar = calendar
        self._days = []

    def change_starting_day(self, date):
        """Change starting day to day from """


class CalendarDay(object):
    """Class representing a day of calendar data."""
    def __init__(self):
        self._scheduled_items = []

    
