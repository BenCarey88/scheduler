"""Wrapper around datetime classes for easier interaction."""

import datetime


class DateTimeError(Exception):
    """Exception class for datetime related errors."""


class BaseDateTimeWrapper(object):
    """Base datetime wrapper class."""

    # Weekday strings
    MON = "Monday"
    TUE = "Tuesday"
    WED = "Wednesday"
    THU = "Thursday"
    FRI = "Friday"
    SAT = "Saturday"
    SUN = "Sunday"
    WEEKDAYS = [MON, TUE, WED, THU, FRI, SAT, SUN]
    NUM_WEEKDAYS = len(WEEKDAYS)

    # Month strings
    JAN = "January"
    FEB = "February"
    MAR = "March"
    APR = "April"
    MAY = "May"
    JUN = "June"
    JUL = "July"
    AUG = "August"
    SEP = "September"
    OCT = "October"
    NOV = "November"
    DEC = "December"
    MONTHS = [JAN, FEB, MAR, APR, MAY, JUN, JUL, AUG, SEP, OCT, NOV, DEC]
    NUM_MONTHS = len(MONTHS)

    def __init__(self, datetime_obj):
        """Initialise base class.

        Args:
            datetime_obj (datetime.datetime, datetime.date, datetime.time):
                datetime object that this is wrapped around.
        """
        self._datetime_obj = datetime_obj

    def string(self):
        """Get string representation of class instance.

        Returns:
            (str): string representation of class instance.
        """
        return str(self._datetime_obj)


class Date(BaseDateTimeWrapper):
    """Wrapper around datetime date class for easy string conversions etc."""
    def __init__(self, year=None, month=None, day=None, _date=None):
        """
        Initialise date item.

        Args:
            year (int or None): year to pass to date or datetime init.
            month (int or None): month to pass to date or datetime init.
            day (int or None): day to pass to date or datetime init.
            _date (datetime.date): date obj to initialise from directly.
                This is for easier use by classmethods, not intended to
                be used by clients.
        """
        if _date is not None:
            self._datetime_obj = _date
        elif all(x is not None for x in (year, month, day)):
            self._datetime_obj = datetime.date(year, month, day)
        else:
            raise DateTimeError(
                "Date class __init__ must provide a year, month and "
                "day attribute, or a datetime.date object"
            )

    @classmethod
    def from_string(cls, date_str):
        """Get Date object from string

        Args:
            datetime_str (str): date string in format:
                yyyy-mm-dd

        Returns:
            (Date): Date object.
        """
        _date = datetime.datetime.strptime(
            date_str,
            "%Y-%m-%d"
        ).date()
        return cls(_date=_date)

    @classmethod
    def now(cls):
        """Return current date.

        Returns:
            (Date): object representing current date.
        """
        return cls(_date=datetime.datetime.now().date())

    def year(self):
        """Get year.

        Returns:
            (int): year of date object.
        """
        return self._datetime_obj.year()

    def month(self):
        """Get month.

        Returns:
            (int): month of date object.
        """
        return self._datetime_obj.month()

    def day(self):
        """Get day.

        Returns:
            (int): self._datetime_obj.day()
        """
        return self._datetime_obj.day()

    def weekday_string(self, short=True):
        """Get string representing weekday.

        Args:
            short (bool): if True, just return the three letter name.

        Returns:
            (str): weekday string.
        """
        weekday_string = self.WEEKDAYS[self.weekday()]
        return weekday_string[:3] if short else weekday_string

    def month_string(self, short=True):
        """Get string representing month.

        Args:
            short (bool): if True, just return the three letter name.

        Returns:
            (str): month string.
        """
        month_string = self.MONTHS[self.month()]
        return month_string[:3] if short else month_string

    def ordinal_string(self):
        """Get day ordinal (eg. 1st, 2nd 3rd etc.).

        Returns:
            (str): day ordinal.
        """
        day = self.day()
        if day == 1:
            return "1st"
        if day == 2:
            return "2nd"
        if day == 3:
            return "3rd"
        return "{0}th"

    def title_string(self, long=False):
        """Get string representing day and date, used for headers.

        This is of the form "Mon 1st", or "Mon 1st Jan 2000".

        Args:
            short (bool): if True, add date and year as well.

        Returns:
            (str): day string.
        """
        string = "{0} {1}".format(
            self.weekday_string(),
            self.ordinal_string()
        )
        if long:
            string = "{0} {1} {2}".format(
                string,
                self.month_string(),
                self.year()
            )
        return string


class Time(BaseDateTimeWrapper):
    """Wrapper around datetime time class for easy string conversions etc."""
    def __init__(self, hour=0, minute=0, second=0, _time=None):
        """
        Initialise time item.

        Args:
            hour (int): year to pass to date or datetime init.
            month (int): month to pass to date or datetime init.
            day (int): day to pass to date or datetime init.
            _time (datetime.time): time obj to initialise from directly.
                This is for easier use by classmethods, not intended to
                be used by clients.
        """
        if _time is not None:
            self._datetime_obj = _time
        self._datetime_obj = datetime.time(hour, minute, second)

    @classmethod
    def from_string(cls, time_str):
        """Create Time from string.

        Args:
            datetime_str (str): date_time string in format:
                hh:mm:ss.ff

        Returns:
            (Time): Time object.
        """
        _time = datetime.datetime.strptime(
            time_str,
            "%H:%M:%S.%f"
        ).time()
        return cls(_time=_time)

    @classmethod
    def now(cls):
        """Return current time.

        Returns:
            (Time): object representing current time.
        """
        return cls(_time=datetime.datetime.now().time())

    def hour(self):
        """Get hour.

        Returns:
            (int): hour of time object.
        """
        return self._datetime_obj.hour()

    def minute(self):
        """Get minute.

        Returns:
            (int): minute of time object.
        """
        return self._datetime_obj.minute()

    def second(self):
        """Get second.

        Returns:
            (int): second of time object.
        """
        return self._datetime_obj.second()

    def title_string(self):
        """Get hour and minute string, used for titles.

        This is of the form "10:30".

        Returns:
            (str) title describing hours and minutes.
        """
        return "{0}:{1}".format(self.hour(), self.minute())


class DateTime(Date, Time):
    """Wrapper around datetime classes allowing easy string conversions etc.

    This inherits from both date and time functions.
    """
    def __init__(
            self,
            year=None,
            month=None,
            day=None,
            hour=0,
            minute=0,
            second=0,
            _datetime=None):
        """Initialise datetime object.

        We should be using the class methods to initialise

        Args:
            year (int or None): year to pass to datetime init.
            month (int or None): month to pass to datetime init.
            day (int or None): day to pass to datetime init.
            hour (int): hour to pass to time or datetime init.
            minute (int): minute to pass to time or datetime init.
            second (int): second to pass to time or datetime init.
            _datetime (datetime.datetime): datetime obj to initialise from
                directly.
        """
        if _datetime:
            self._datetime_obj = _datetime
        elif all(x is not None for x in (year, month, day)):
            self._datetime_obj = datetime.datetime(
                year,
                month,
                day,
                hour,
                minute,
                second
            )
        else:
            raise DateTimeError(
                "DateTime class __init__ must provide a year, month and "
                "day attribute, or a datetime.datetime object"
            )

    @classmethod
    def from_string(cls, datetime_str):
        """Create DateTime object from string

        Args:
            datetime_str (str): time string in format:
                yyyy-mm-dd hh:mm:ss.ff

        Returns:
            (DateTime): DateTime object.
        """
        _datetime = datetime.datetime.strptime(
            datetime_str,
            "%Y-%m-%d %H:%M:%S.%f"
        )
        return cls(_datetime=_datetime)

    @classmethod
    def from_date_and_time(cls, date, time):
        """Create DateTime class instance from Date and Time class instances.

        Args:
            date (Date): date instance.
            time (Time): time instance.

        Returns:
            (DateTime): DateTime object.
        """
        _datetime = datetime.datetime.combine(
            date._datetime_obj,
            time._datetime_obj,
        )
        return cls(_datetime=_datetime)

    @classmethod
    def now(cls):
        """Return current datetime.

        Returns:
            (DateTime): object representing current date and time.
        """
        return cls(_datetime=datetime.datetime.now())

    def date(self):
        """Get Date object.

        Returns:
            (Date): Date object.
        """
        return Date(_date=self._datetime_obj.date())

    def date_string(self):
        """Get string representing date.

        Returns:
            (str): date string.
        """
        return self.date().string()

    def time(self):
        """Get Time object.

        Returns:
            (Time): Time object.
        """
        return Time(_time=self._datetime_obj.time())

    def time_string(self):
        """Get string representing time.

        Returns:
            (str): time string.
        """
        return self.time().string()

    def title_string(self, long=False):
        """Get title string for use in headers etc.

        Args:
            (str): string to use for titles.
        """
        return "{0} {1}".format(
            self.date().title_string(long=True),
            self.time().title_string()
        )
