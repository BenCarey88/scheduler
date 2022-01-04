"""Wrapper around datetime classes for easier interaction."""

import calendar
import datetime
import math


class DateTimeError(Exception):
    """Exception class for datetime related errors."""


class TimeDelta(object):
    """Wrapper around datetime.timedelta class.

    We implement two additions to the datetime.timedelta usage:
        - datetime.timedelta doesn't allow month or year values since these can
            represent varying amounts of time. We implement these by storing
            them as extra attributes which we only interpret depending on the
            during addition/subtraction with a Date, Time or DateTime object.
            Note though that if these are used we'll no longer be able to use
            methods like total_seconds or the days property.
        - datetime.timedelta classes can only be added to datetime or date
            objects. We allow adding TimeDeltas to Time objects too and just
            ignoring the date part of the timedelta.
    """
    def __init__(
            self,
            years=0,
            months=0,
            weeks=0,
            days=0,
            hours=0,
            minutes=0,
            seconds=0,
            _timedelta=None):
        """Initialise timedelta object representing a difference in date/time.

        Args:
            years (int): number of years.
            months (int): number of months.
            weeks (int): number of weeks.
            days (int): number of days.
            hours (int): number of hours.
            minutes (int): number of minutes.
            seconds (int): number of seconds.
            _timedelta (datetime.timedelta or None): datetime obj to initialise
                from directly.
        """
        self._years = int(years)
        self._months = int(months)
        if _timedelta is not None:
            if isinstance(_timedelta, datetime.timedelta):
                self._timedelta_obj = _timedelta
            else:
                raise DateTimeError(
                    "_timedelta param in TimeDelta __init__ must be None or a "
                    "datetime.timedelta object, not {0}".format(
                        type(_timedelta)
                    )
                )
        else:
            self._timedelta_obj = datetime.timedelta(
                weeks=weeks,
                days=days,
                hours=hours,
                minutes=minutes,
                seconds=seconds
            )

    def __add__(self, timedelta_or_datetime):
        """Add this to another timedelta, or to a BaseDateTimeWrapper object.

        Args:
            timedelta_or_datetime (TimeDelta, datetime.timedelta,
            or BaseDateTimeWrapper):
                time delta to add, or wrapped datetime object that we're adding
                this to.

        Returns:
            (TimeDelta or BaseDateTimeWrapper): modified timedelta, or modified
                datetime object.
        """
        if isinstance(timedelta_or_datetime, datetime.timedelta):
            return TimeDelta(
                years=self._years,
                months=self._months,
                _timedelta=(self._timedelta_obj + timedelta_or_datetime)
            )
        if isinstance(timedelta_or_datetime, TimeDelta):
            return TimeDelta(
                years=(self._years + timedelta_or_datetime._years),
                months=(self._months + timedelta_or_datetime._months), 
                _timedelta=(
                    self._timedelta_obj + timedelta_or_datetime._timedelta_obj
                )
            )
        if isinstance(timedelta_or_datetime, BaseDateTimeWrapper):
            # use BaseDateTimeWrapper __add__
            return timedelta_or_datetime + self
        raise DateTimeError(
            "Supported args to TimeDelta addition are: TimeDelta, "
            "datetime.timedelta or BaseDateTimeWrapper, not {0}".format(
                type(timedelta_or_datetime)
            )
        )

    def __sub__(self, timedelta):
        """Subtract another timedelta from this.

        Args:
            timedelta (TimeDelta or  datetime.timedelta): time delta to
                subtract.

        Returns:
            (TimeDelta): modified timedelta.
        """
        if isinstance(timedelta, datetime.timedelta):
            return TimeDelta(
                years=self._years,
                months=self._months,
                _timedelta=(self._timedelta_obj - timedelta)
            )
        if isinstance(timedelta, TimeDelta):
            return TimeDelta(
                years=(self._years - timedelta._years),
                months=(self._months - timedelta._months),
                _timedelta=self._timedelta_obj - timedelta._timedelta_obj
            )
        raise DateTimeError(
            "Supported args to TimeDelta subtraction are: TimeDelta or "
            "datetime.timedelta, not {0}".format(type(timedelta))
        )

    def __neg__(self):
        """Get negation of timedelta.

        Returns:
            (TimeDelta): negative of time delta.
        """
        return TimeDelta(
            years=-self._years,
            months=-self._months,
            _timedelta=-self._timedelta_obj
        )

    def __mul__(self, scalar):
        """Multiply timedelta by a scalar.

        Note that this may give dodgy results if _years or _months attributes
        are nonzero, particularly if the scalar is not integral.

        Args:
            scalar (int, float): scalar to multiply by.

        Returns:
            (TimeDelta): modified time delta.
        """
        if not isinstance(scalar, (int, float)):
            raise DateTimeError(
                "Args to TimeDelta multiplication must be int or float, "
                "not {0}".format(type(scalar))
            )
        return TimeDelta(
            years=(self._years * scalar),
            months=(self._months * scalar),
            _timedelta=(self._timedelta_obj * scalar)
        )

    def __rmul__(self, scalar):
        """Right-multiply timedelta by a scalar.

        Args:
            scalar (int, float): scalar to multiply by.

        Returns:
            (TimeDelta): modified time delta.
        """
        return self.__mul__(scalar)

    def __div__(self, scalar):
        """Divide timedelta by a scalar.

        Args:
            scalar (int, float): scalar to divide by.

        Returns:
            (TimeDelta): modified time delta.
        """
        return self.__mul__(1 / scalar)

    def __truediv__(self, scalar):
        """Divide timedelta by a scalar.

        Args:
            scalar (int, float): scalar to divide by.

        Returns:
            (TimeDelta): modified time delta.
        """
        return self.__div__(scalar)

    def __lt__(self, time_delta):
        """Compare to other time_delta.

        Args:
            time_delta (TimeDelta): object to compare to.

        Returns:
            (bool): whether this is less than time_delta.
        """
        self._check_no_years_or_months()
        return self._timedelta_obj < time_delta._timedelta_obj

    def __gt__(self, time_delta):
        """Compare to other time_delta.

        Args:
            time_delta (TimeDelta): object to compare to.

        Returns:
            (bool): whether this is greater than time_delta.
        """
        self._check_no_years_or_months()
        return self._timedelta_obj > time_delta._timedelta_obj

    def __le__(self, time_delta):
        """Compare to other time_delta.

        Args:
            time_delta (TimeDelta): object to compare to.

        Returns:
            (bool): whether this is less than or equal to time_delta.
        """
        self._check_no_years_or_months()
        return self._timedelta_obj <= time_delta._timedelta_obj

    def __ge__(self, time_delta):
        """Compare to other time_delta.

        Args:
            time_delta (TimeDelta): object to compare to.

        Returns:
            (bool): whether this is greater than or equal to time_delta.
        """
        self._check_no_years_or_months()
        return self._timedelta_obj >= time_delta._timedelta_obj

    def _check_no_years_or_months(self):
        """Convenience method to raise error if years or months attrs aren't 0.

        Since years and months don't have fixed timespans then we can't perform
        any methods that get an exact timespan from a TimeDelta if these are
        nonzero, so this error will be raised.
        """
        if self._years or self._months:
            raise DateTimeError(
                "Can't return time values for TimeDelta class with nonzero "
                "_year or _month attributes."
            )

    @property
    def days(self):
        """Get number of days in time delta.

        Returns:
            (int): days of timedelta object.
        """
        self._check_no_years_or_months()
        return self._timedelta_obj.days

    def total_seconds(self):
        """Get total number of seconds of time delta.

        Returns:
            (int): total number of seconds.
        """
        self._check_no_years_or_months()
        return self._timedelta_obj.total_seconds()

    def __repr__(self):
        """Override string representation of self.

        Return:
            (str): string representation.
        """
        return str(self._timedelta_obj)

    def __str__(self):
        """Override string representation of self.

        Return:
            (str): string representation.
        """
        return self.__repr__()


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

    @classmethod
    def weekday_string_from_int(cls, weekday, short=True):
        """Get weekday string from integer representing weekday.

        Args:
            weekday (int): integer representing weekday.
            short (bool): if True, just return the three letter name.

        Returns:
            (str): weekday string.
        """
        weekday_string = cls.WEEKDAYS[weekday]
        return weekday_string[:3] if short else weekday_string

    @classmethod
    def weekday_int_from_string(cls, weekday_string):
        """Get string representing weekday.

        Args:
            weekday_string (str): string representing weekday (short or long).

        Returns:
            (int): integer value of that weekday.
        """
        for i, weekday in enumerate(cls.WEEKDAYS):
            if weekday.startswith(weekday_string):
                return i
        raise DateTimeError(
            "String {0} cannot be converted to weekday".format(weekday_string)
        )

    # TODO: when using these bool args with defaults, default should be False
    # ie. this should be long=False, or short=False if we want default as long
    @classmethod
    def month_string_from_int(cls, month, short=True):
        """Get string representing month.

        Args:
            month (int): integer representing month.
            short (bool): if True, just return the three letter name.

        Returns:
            (str): month string.
        """
        month_string = cls.MONTHS[month - 1]
        return month_string[:3] if short else month_string

    @classmethod
    def month_int_from_string(cls, month_string):
        """Get string representing month.

        Args:
            month_string (str): string representing month (short or long).

        Returns:
            (int): integer value of that month.
        """
        for i, month in enumerate(cls.MONTHS):
            if month.startswith(month_string):
                return i + 1
        raise DateTimeError(
            "String {0} cannot be converted to month".format(month_string)
        )

    @staticmethod
    def num_days_in_month(year, month):
        """Reimplement python calendar module monthrange function.

        Args:
            year (int): year to check.
            month (int): month to check.

        Returns:
            (int): number of days in given month on given year.
        """
        return calendar.monthrange(year, month)[1]

    def __eq__(self, date_time):
        """Check if this is equal to another date time object.

        Args:
            date_time (BaseDateTimeWrapper or datetime.datetime, datetime.time,
                datetime.date): object to check equality with.

        Returns:
            (bool): whether this equals date_time.
        """
        if isinstance(date_time, BaseDateTimeWrapper):
            return self._datetime_obj == date_time._datetime_obj
        elif isinstance(
                date_time, (datetime.datetime, datetime.date, datetime.time)):
            return self._datetime_obj == date_time
        return False

    def __ne__(self, date_time):
        """Check if this is equal to another date time object.

        Args:
            date_time (BaseDateTimeWrapper or datetime.datetime, datetime.time,
                datetime.date): object to check equality with.

        Returns:
            (bool): whether this does not equal date_time.
        """
        if isinstance(date_time, BaseDateTimeWrapper):
            return self._datetime_obj != date_time._datetime_obj
        elif isinstance(
                date_time, (datetime.datetime, datetime.date, datetime.time)):
            return self._datetime_obj != date_time
        return False

    def __lt__(self, date_time):
        """Compare to other date time.

        Args:
            date_time (BaseDateTimeWrapper or datetime.datetime, datetime.time,
                datetime.date): object to compare to.

        Returns:
            (bool): whether this is less than date_time.
        """
        if isinstance(date_time, BaseDateTimeWrapper):
            return self._datetime_obj < date_time._datetime_obj
        elif isinstance(
                date_time, (datetime.datetime, datetime.date, datetime.time)):
            return self._datetime_obj < date_time
        return False

    def __gt__(self, date_time):
        """Compare to other date time.

        Args:
            date_time (BaseDateTimeWrapper or datetime.datetime, datetime.time,
                datetime.date): object to compare to.

        Returns:
            (bool): whether this is greater than date_time.
        """
        if isinstance(date_time, BaseDateTimeWrapper):
            return self._datetime_obj > date_time._datetime_obj
        elif isinstance(
                date_time, (datetime.datetime, datetime.date, datetime.time)):
            return self._datetime_obj > date_time
        return False

    def __le__(self, date_time):
        """Compare to other date time.

        Args:
            date_time (BaseDateTimeWrapper or datetime.datetime, datetime.time,
                datetime.date): object to compare to.

        Returns:
            (bool): whether this is less than or equal to date_time.
        """
        if isinstance(date_time, BaseDateTimeWrapper):
            return self._datetime_obj <= date_time._datetime_obj
        elif isinstance(
                date_time, (datetime.datetime, datetime.date, datetime.time)):
            return self._datetime_obj <= date_time
        return False

    def __ge__(self, date_time):
        """Compare to other date time.

        Args:
            date_time (BaseDateTimeWrapper or datetime.datetime, datetime.time,
                datetime.date): object to compare to.

        Returns:
            (bool): whether this is greater than or equal to date_time.
        """
        if isinstance(date_time, BaseDateTimeWrapper):
            return self._datetime_obj >= date_time._datetime_obj
        elif isinstance(
                date_time, (datetime.datetime, datetime.date, datetime.time)):
            return self._datetime_obj >= date_time
        return False

    def __hash__(self):
        """Hash this object using the datetime_obj hash.

        Returns:
            (int): the object hash.
        """
        return hash(self._datetime_obj)

    def __add__(self, time_delta):
        """Add time_delta to date_time object.

        Args:
            time_delta (TimeDelta or datetime.timedelta): time delta to add.

        Returns:
            (BaseDateTimeWrapper): return value is implemented in the subclasses.
        """
        if not isinstance(time_delta, (TimeDelta, datetime.timedelta)):
            raise DateTimeError(
                "DateTime addition requires TimeDelta or "
                "datetime.timedelta object, not {0}".format(type(time_delta))
            )

    def __sub__(self, timedelta_or_datetime):
        """Subtract time_delta from date_time object.

        Note that there's a potential for ambiguity here when subtracting a
        datetime object: if, say, we add TimeDelta(months=1) to a given date
        in october, and then subtract that date from the result, we'll end
        up with TimeDelta(days=31), which is not always the same thing. This
        ambiguity must be kept in mind whenever using the __sub__ method on
        two date_time objects.

        Args:
            timedelta_or_datetime (TimeDelta or datetime.timedelta or
                BaseDateTimeWrapper): time delta or date time to subtract.

        Returns:
            (BaseDateTimeWrapper or TimeDelta): return value is implemented in
                the subclasses.
        """
        accepted_classes = (
            TimeDelta,
            datetime.timedelta,
            self.__class__,
            self._datetime_obj.__class__
        )
        if not isinstance(timedelta_or_datetime, accepted_classes):
            raise DateTimeError(
                "DateTime __sub__ requires one of the following arguments: "
                "TimeDelta, datetime.timedelta, {0}, {1}, not {2}".format(
                    self.__class__,
                    self._datetime_obj.__class__,
                    type(timedelta_or_datetime)
                )
            )

    # TODO: add a bunch of args to string method for subclasses, and add
    # corresponding args in from_string methods
    def string(self):
        """Get string representation of class instance.

        This should be the same format as the string used by the from_string
        classmethod.

        Returns:
            (str): string representation of class instance.
        """
        return str(self._datetime_obj)

    def __repr__(self):
        """Override string representation of self.

        Return:
            (str): string representation.
        """
        return self.string()

    def __str__(self):
        """Override string representation of self.

        Return:
            (str): string representation.
        """
        return self.string()


class Date(BaseDateTimeWrapper):
    """Wrapper around datetime date class for easy string conversions etc."""
    def __init__(self, year=None, month=None, day=None, _date=None):
        """Initialise date item.

        Args:
            year (int or None): year to pass to date or datetime init.
            month (int or None): month to pass to date or datetime init.
            day (int or None): day to pass to date or datetime init.
            _date (datetime.date): date obj to initialise from directly.
                This is for easier use by classmethods, not intended to
                be used by clients.
        """
        if _date is not None:
            if isinstance(_date, datetime.date):
                self._datetime_obj = _date
            else:
                raise DateTimeError(
                    "_date param in Date __init__ must be None or a "
                    "datetime.date object, not {0}".format(type(_date))
                )
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

    def __add__(self, time_delta):
        """Add time_delta to date object.

        Args:
            time_delta (TimeDelta or datetime.timedelta): time delta to add.

        Returns:
            (Date): modified date object.
        """
        super(Date, self).__add__(time_delta)
        if isinstance(time_delta, datetime.timedelta):
            return Date(
                _date=(self._datetime_obj + time_delta)
            )
        elif isinstance(time_delta, TimeDelta):
            date = self._datetime_obj
            # calculate years and months first.
            if time_delta._months or time_delta._years:
                month_total = self.month + time_delta._months
                new_month = (month_total - 1) % 12 + 1
                additional_years = math.floor((month_total - 1)/12)
                new_year = self.year + time_delta._years + additional_years
                date = datetime.date(new_year, new_month, self.day)
            # and now add rest of datetime.
            return Date(
                _date=(date + time_delta._timedelta_obj)
            )

    def __sub__(self, timedelta_or_date):
        """Subtract time_delta or date from date object.

        See base class docstring for explanation of ambiguity in this method's
        result.

        Args:
            timedelta_or_date (TimeDelta, datetime.timedelta, datetime.date,
                or Date): time delta or date to subtract.

        Returns:
            (Date or TimeDelta): modified Date object, if subtracting a
                timedelta, or new timedelta, if subtracting another date.
        """
        super(Date, self).__sub__(timedelta_or_date)
        if isinstance(timedelta_or_date, (TimeDelta, datetime.timedelta)):
            return self + (-timedelta_or_date)
        elif isinstance(timedelta_or_date, datetime.date):
            return TimeDelta(
                _timedelta=(
                    self._datetime_obj - timedelta_or_date
                )
            )
        elif isinstance(timedelta_or_date, Date):
            return TimeDelta(
                _timedelta=(
                    self._datetime_obj - timedelta_or_date._datetime_obj
                )
            )

    @property
    def year(self):
        """Get year.

        Returns:
            (int): year of date object.
        """
        return self._datetime_obj.year

    @property
    def month(self):
        """Get month.

        Returns:
            (int): month of date object.
        """
        return self._datetime_obj.month

    @property
    def day(self):
        """Get day.

        Returns:
            (int): day of date object.
        """
        return self._datetime_obj.day

    @property
    def weekday(self):
        """Get weekday.

        Returns:
            (int): integerr from 0 to 6 representing weekday.
        """
        return self._datetime_obj.weekday()

    def weekday_string(self, short=True):
        """Get string representing weekday.

        Args:
            short (bool): if True, just return the three letter name.

        Returns:
            (str): weekday string.
        """
        return self.weekday_string_from_int(self.weekday)

    def month_string(self, short=True):
        """Get string representing month.

        Args:
            short (bool): if True, just return the three letter name.

        Returns:
            (str): month string.
        """
        return self.month_string_from_int(self.month)

    def ordinal_string(self):
        """Get day ordinal (eg. 1st, 2nd 3rd etc.).

        Returns:
            (str): day ordinal.
        """
        day = self.day
        if day == 1:
            return "1st"
        if day == 2:
            return "2nd"
        if day == 3:
            return "3rd"
        return "{0}th".format(self.day)


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
            if isinstance(_time, datetime.time):
                self._datetime_obj = _time
            else:
                raise DateTimeError(
                    "_time param in Time __init__ must be None or a "
                    "datetime.time object, not {0}".format(type(_time))
                )
        else:
            self._datetime_obj = datetime.time(hour, minute, second)

    @classmethod
    def now(cls):
        """Return current time.

        Returns:
            (Time): object representing current time.
        """
        return cls(_time=datetime.datetime.now().time())

    @classmethod
    def from_string(cls, time_str, short=True):
        """Create Time from string.

        Args:
            datetime_str (str): date_time string in format: hh:mm:ss.ff
            short (bool): if true, the format should be: hh:mm

        Returns:
            (Time): Time object.
        """
        if short:
            time_str = "{0}:00.00".format(time_str)
        _time = datetime.datetime.strptime(
            time_str,
            "%H:%M:%S.%f"
        ).time()
        return cls(_time=_time)

    def string(self, short=True):
        """Get string representation of class instance.

        This should be the same format as the string used by the from_string
        classmethod.

        Args:
            short (bool): if true, use form hh:mm.

        Returns:
            (str): string representation of class instance.
        """
        if short:
            return "{0}:{1}".format(
                str(self.hour).zfill(2),
                str(self.minute).zfill(2)
            )
        return str(self._datetime_obj)

    def __add__(self, time_delta):
        """Add time_delta to date object.

        Args:
            time_delta (TimeDelta or datetime.timedelta): time delta to add.

        Returns:
            (Date): modified date object.
        """
        super(Time, self).__add__(time_delta)
        temp_datetime = datetime.datetime.combine(
            datetime.date(1000,1,1),
            self._datetime_obj
        )
        if isinstance(time_delta, datetime.timedelta):
            temp_datetime += time_delta
        elif isinstance(time_delta, TimeDelta):
            temp_datetime += time_delta._timedelta_obj
        return Time(_time=temp_datetime.time())

    def __sub__(self, timedelta_or_time):
        """Subtract time_delta or time from time object.

        Args:
            timedelta_or_time (TimeDelta, datetime.timedelta, datetime.time,
                or Time): time delta or time to subtract.

        Returns:
            (Time or TimeDelta): modified Time object, if subtracting a
                timedelta, or new timedelta, if subtracting another time.
        """
        super(Time, self).__sub__(timedelta_or_time)
        if isinstance(timedelta_or_time, (TimeDelta, datetime.timedelta)):
            return self + (-timedelta_or_time)
        temp_date = datetime.date(1000,1,1)
        temp_datetime = datetime.datetime.combine(
            temp_date,
            self._datetime_obj
        )
        if isinstance(timedelta_or_time, datetime.time):
            time_delta = temp_datetime - datetime.datetime.combine(
                temp_date,
                timedelta_or_time
            )
        elif isinstance(timedelta_or_time, Time):
            time_delta = temp_datetime - datetime.datetime.combine(
                temp_date,
                timedelta_or_time._datetime_obj
            )
        return TimeDelta(_timedelta=time_delta)

    @property
    def hour(self):
        """Get hour.

        Returns:
            (int): hour of time object.
        """
        return self._datetime_obj.hour

    @property
    def minute(self):
        """Get minute.

        Returns:
            (int): minute of time object.
        """
        return self._datetime_obj.minute

    @property
    def second(self):
        """Get second.

        Returns:
            (int): second of time object.
        """
        return self._datetime_obj.second


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
            _datetime (datetime.datetime or None): datetime obj to initialise
                from directly.
        """
        if _datetime is not None:
            if isinstance(_datetime, datetime.datetime):
                self._datetime_obj = _datetime
            else:
                raise DateTimeError(
                    "_datetime param in DateTime __init__ must be None or a "
                    "datetime.datetime object, not {0}".format(type(_datetime))
                )
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
            "%Y-%m-%d %H:%M:%S"
        )
        return cls(_datetime=_datetime)

    def string(self):
        """Get string representation of class instance.

        This should be the same format as the string used by the from_string
        classmethod.

        Returns:
            (str): string representation of class instance.
        """
        return str(self._datetime_obj)

    def __add__(self, time_delta):
        """Add time_delta to datetime object.

        Args:
            time_delta (TimeDelta or datetime.timedelta): time delta to add.

        Returns:
            (DateTime): modified date time object.
        """
        super(DateTime, self).__add__(time_delta)
        if isinstance(time_delta, datetime.timedelta):
            return DateTime(
                _datetime=(self._datetime_obj + time_delta)
            )
        else:
            _datetime = self._datetime_obj
            # calculate years and months first.
            if time_delta._months or time_delta._years:
                month_total = self.month + time_delta._months
                new_month = (month_total - 1) % 12 + 1
                additional_years = math.floor((month_total - 1)/12)
                new_year = self.year + time_delta._years + additional_years
                _datetime = datetime.datetime(
                    new_year,
                    new_month,
                    self.day,
                    self.hour,
                    self.minute,
                    self.second
                )
            # and now add rest of timedelta.
            return DateTime(
                _datetime=(_datetime + time_delta._timedelta_obj)
            )

    def __sub__(self, timedelta_or_datetime):
        """Subtract time_delta or date_time from date object.

        See base class docstring for explanation of ambiguity in this method's
        result.

        Args:
            timedelta_or_datetime (TimeDelta, datetime.timedelta,
                datetime.datetime or DateTime): time delta or date to subtract.

        Returns:
            (DateTime or TimeDelta): modified DateTime object, if
                subtracting a timedelta, or new timedelta, if subtracting
                another date.
        """
        super(DateTime, self).__sub__(timedelta_or_datetime)
        if isinstance(timedelta_or_datetime, (TimeDelta, datetime.timedelta)):
            return self + (-timedelta_or_datetime)
        elif isinstance(timedelta_or_datetime, datetime.datetime):
            return TimeDelta(
                _timedelta=(
                    self._datetime_obj - timedelta_or_datetime
                )
            )
        elif isinstance(timedelta_or_datetime, DateTime):
            return TimeDelta(
                _timedelta=(
                    self._datetime_obj - timedelta_or_datetime._datetime_obj
                )
            )

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
