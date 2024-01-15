"""Class to define a repeat pattern for scheduled and planned items."""

from scheduler.api.common.date_time import Date, TimeDelta
from scheduler.api.serialization.serializable import (
    NestedSerializable,
    SaveType,
)


class RepeatPatternError(Exception):
    """Generic exception for repeat pattern errors."""


# TODO: for neatness, make this match with other classes that don't need
# file serialization but do use to_dict and from_dict methods (eg.
# TaskHistory, Filter and TrackerTarget classes) - either these should all
# subclass from NestedSerializable with SaveType.NESTED or none should).
class RepeatPattern(NestedSerializable):
    """Class to determine the dates of a repeating scheduled item."""
    _SAVE_TYPE = SaveType.NESTED

    INITIAL_DATES_KEY = "initial_dates"
    TIMEDELTA_GAP_KEY = "timedelta_gap"
    REPEAT_TYPE_KEY = "repeat_type"
    END_DATE_KEY = "end_date"

    DAY_REPEAT = "day_repeat"
    WEEK_REPEAT = "week_repeat"
    MONTH_REPEAT = "month_repeat"
    YEAR_REPEAT = "year_repeat"

    def __init__(
            self,
            inital_date_pattern,
            timedelta_gap,
            repeat_type=None,
            end_date=None):
        """Initialise class.

        Args:
            initial_date_pattern (list(Date)): list of first dates of repeating
                item.
            timedelta_gap (TimeDelta): gap of time after first date before
                pattern repeats.
            repeat_type (str or None): type of repeating used.
            end_date (Date or None): end date, if one exists.
        """
        super(RepeatPattern, self).__init__()
        self._initial_date_pattern = inital_date_pattern
        if inital_date_pattern[0] + timedelta_gap <= inital_date_pattern[-1]:
            raise RepeatPatternError(
                "RepeatPattern timedelta_gap is too small for given range"
            )
        self._pattern_size = len(inital_date_pattern)
        self._gap = timedelta_gap
        self._gap_multiplier = 1
        self._dates = [date for date in inital_date_pattern]
        self._repeat_type = repeat_type or self.DAY_REPEAT
        self._end_date = end_date

    def _get_hashable_attrs(self):
        """Get hashable attributes of object.

        Returns:
            (tuple): self._initial_date_pattern, self._gap, self._end_date
                and self._repeat_type
        """
        return (
            tuple(self._initial_date_pattern),
            self._gap,
            self._end_date,
            self._repeat_type
        )

    def __eq__(self, repeat_pattern):
        """Check if this is equal to another class instance.

        Args:
            repeat_pattern (RepeatPattern): other instance to
                compare to.

        Returns:
            (bool): whether or not instances are equal.        
        """
        return (
            isinstance(repeat_pattern, RepeatPattern) and
            self._get_hashable_attrs() == repeat_pattern._get_hashable_attrs()
        )

    def __ne__(self, repeat_pattern):
        """Check if this is not equal to another class instance.

        Args:
            repeat_pattern (RepeatPattern): other instance to
                compare to.

        Returns:
            (bool): whether or not instances are not equal.        
        """
        return not self.__eq__(repeat_pattern)

    def __hash__(self):
        """Get hash of repeat type.

        Returns:
            (int): hashed value.
        """
        return hash(self._get_hashable_attrs())

    @property
    def initial_dates(self):
        """Get dates of initial repeat pattern.

        Returns:
            (list(Date)): list of days of initial pattern.
        """
        return self._initial_date_pattern

    @property
    def start_date(self):
        """Get start date of repeat pattern.
        
        Returns:
            (Date): date repeat pattern starts at.
        """
        return self._initial_date_pattern[0]
    
    @property
    def end_date(self):
        """Get end date of repeat pattern, if one exists.

        Returns:
            (Date or None): end date of pattern, if exists.
        """
        return self._end_date

    @property
    def repeat_type(self):
        """Return repeat type of pattern.

        Returns:
            (str): repeat type, ie. whether this repeats based on days,
                months, weeks or years.
        """
        return self._repeat_type

    @classmethod
    def day_repeat(cls, inital_date_pattern, day_gap, end_date=None):
        """Initialise class as pattern of dates with gap of days in between.

        Args:
            initial_date_pattern (list(Date)): list of first dates of repeating
                item.
            day_gap (int): number of days before pattern repeats.
            end_date (Date or None): end date, if one exists.

        Returns:
            (ScheduledItemRepeat): class instance.
        """
        return cls(
            inital_date_pattern,
            TimeDelta(days=day_gap),
            cls.DAY_REPEAT,
            end_date,
        )

    @classmethod
    def week_repeat(cls, starting_day, weekdays, week_gap=1, end_date=None):
        """Initialise class as set of weekdays with week gap in between.

        Args:
            starting_day (Date): first date of scheduled item.
            weekdays (list(str)): list of weekdays that this will
                repeat on.
            week_gap (int): number of weeks before repeating.
            end_date (Date or None): end date, if one exists.

        Returns:
            (ScheduledItemRepeat): class instance.
        """
        weekdays = [
            Date.weekday_int_from_string(weekday) for weekday in weekdays
        ]
        def days_from_start(weekday_int):
            return (weekday_int - starting_day.weekday) % 7
        weekdays.sort(key=days_from_start)
        initial_date_pattern = []
        for weekday in weekdays:
            initial_date_pattern.append(
                starting_day + TimeDelta(days=days_from_start(weekday))
            )
        return cls(
            initial_date_pattern,
            TimeDelta(days=7*week_gap),
            cls.WEEK_REPEAT,
            end_date,
        )

    @classmethod
    def month_repeat(cls, inital_date_pattern, month_gap=1, end_date=None):
        """Initialise class as pattern of dates with month gap in between.

        Args:
            initial_date_pattern (list(Date)): list of first dates of repeating
                item.
            month_gap (int): number of months before pattern repeats.
            end_date (Date or None): end date, if one exists.

        Returns:
            (ScheduledItemRepeat): class instance.
        """
        return cls(
            inital_date_pattern,
            TimeDelta(months=month_gap),
            cls.MONTH_REPEAT,
            end_date,
        )

    @classmethod
    def year_repeat(cls, inital_date_pattern, year_gap=1, end_date=None):
        """Initialise class as pattern of dates with year gap in between.

        Args:
            initial_date_pattern (list(Date)): list of first dates of repeating
                item.
            year_gap (int): number of years before pattern repeats.
            end_date (Date or None): end date, if one exists.

        Returns:
            (ScheduledItemRepeat): class instance.
        """
        return cls(
            inital_date_pattern,
            TimeDelta(years=year_gap),
            cls.YEAR_REPEAT,
            end_date,
        )

    def _update_to_date(self, date):
        """Update internal list of dates to include all before given date.

        Args:
            date (Date): date to update to.
        """
        if self._end_date is not None:
            date = min(date, self._end_date)
        while self._dates[-1] < date:
            for initial_date in self._initial_date_pattern:
                self._dates.append(
                    initial_date + self._gap * self._gap_multiplier
                )
            self._gap_multiplier += 1
        # NOTE that this means that self._dates MAY contain dates
        # slightly beyond end_date, so this needs to be taken into
        # account in check_date and dates_between methods

    def check_date(self, date):
        """Check if the repeating item will fall on the given date.

        Args:
            date (Date): date to check.

        Returns:
            (bool): whether or not item falls on given date.
        """
        self._update_to_date(date)
        if self._end_date is not None and date > self._end_date:
            return False
        return (date in self._dates)

    def dates_between(self, start_date, end_date):
        """Get dates in repeating pattern between the two given dates.

        Args:
            start_date (Date): start date. This is inclusive (ie. included
                in output).
            end_date (Date): end date. This is inclusive (ie. included in
                output).

        Yields:
            (Date): all dates in pattern between the two dates.
        """
        self._update_to_date(end_date)
        for date in self._dates:
            if date < start_date:
                continue
            if date > self._end_date:
                # self._dates may contain dates > self._end_date - we need to
                # skip these as they are not actually part of the pattern
                break
            elif start_date <= date <= end_date:
                yield date
            else:
                break

    def check_end_date_validity(self):
        """Check whether end date is valid.

        Returns:
            (bool): whether end date is valid or not. The end date is invalid
                if it is too early and hence before one of the initial dates.
        """
        if self._end_date is None:
            # having no end date is always valid
            return True
        for date in self._initial_date_pattern:
            if self._end_date < date:
                return False
        return True

    def summary_string(self):
        """Get string summarising the repeat pattern to display in ui.

        Return:
            (str): string summarising the repeat pattern
        """
        num_days = len(self._initial_date_pattern)
        if num_days == 1:
            num_days_string ="Once"
        elif num_days == 2:
            num_days_string = "Twice"
        else:
            num_days_string = "{0} times".format(num_days)

        def get_repeat_time_string(repeat_type, gap_size):
            if gap_size == 1:
                return "a {0}".format(repeat_type)
            return "every {0} {1}s".format(gap_size, repeat_type)

        if self.repeat_type == self.DAY_REPEAT:
            repeat_time_string = get_repeat_time_string(
                "day",
                self._gap.days
            )
        elif self.repeat_type == self.WEEK_REPEAT:
            repeat_time_string = get_repeat_time_string(
                "week",
                int(self._gap.days / 7)
            )
        elif self.repeat_type == self.MONTH_REPEAT:
            repeat_time_string = get_repeat_time_string(
                "month",
                self._gap.months
            )
        elif self.repeat_type == self.WEEK_REPEAT:
            repeat_time_string = get_repeat_time_string(
                "year",
                self._gap.years
            )

        return "{0} {1}".format(num_days_string, repeat_time_string)

    def __str__(self):
        """Get string representation of self.

        Returns:
            (str): summary string.
        """
        return self.summary_string()

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = {
            self.INITIAL_DATES_KEY: [
                date.string() for date in self._initial_date_pattern
            ],
            self.TIMEDELTA_GAP_KEY: self._gap.string(),
            self.REPEAT_TYPE_KEY: self.repeat_type
        }
        if self._end_date:
            dict_repr[self.END_DATE_KEY] = self._end_date.string()
        return dict_repr

    @classmethod
    def from_dict(cls, dict_repr):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.

        Returns:
            (RepeatPattern or None): repeat pattern, if can be
                initialised.
        """
        initial_dates = [
            Date.from_string(date)
            for date in dict_repr.get(cls.INITIAL_DATES_KEY, [])
        ]
        timedelta_gap = TimeDelta.from_string(
            dict_repr.get(cls.TIMEDELTA_GAP_KEY)
        )
        if not initial_dates or not timedelta_gap:
            return None
        end_date = None
        if dict_repr.get(cls.END_DATE_KEY):
            # TODO: should this have error handling? Return None? Continue?
            end_date = Date.from_string(dict_repr.get(cls.END_DATE_KEY))
        return cls(
            initial_dates,
            timedelta_gap,
            dict_repr.get(cls.REPEAT_TYPE_KEY),
            end_date,
        )
