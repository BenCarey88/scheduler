"""Classes representing a time period of calendar data."""

from collections import OrderedDict
from contextlib import contextmanager

from scheduler.api.enums import TimePeriod
from scheduler.api.common.date_time import (
    Date,
    DateTimeError,
    TimeDelta
)
from scheduler.api.common.object_wrappers import HostedDataList
from scheduler.api.serialization.serializable import (
    NestedSerializable,
    SaveType,
    SerializableFileTypes
)
from .scheduled_item import ScheduledItem
from .planned_item import PlannedItem


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
        super(BaseCalendarPeriod, self).__init__()
        self._calendar = calendar

    @property
    def calendar(self):
        """Get root calendar object.

        Returns:
            (Calendar): calendar root object.
        """
        return self._calendar

    def next(self):
        """Get calendar period starting immediately after this one ends.

        Returns:
            (BaseCalendarPeriod): instance of this class starting after
                end of this one.
        """
        raise NotImplementedError(
            "next is implemented in BaseCalendarPeriod subclasses."
        )

    def prev(self):
        """Get calendar period starting immediately before this one begins.

        Returns:
            (BaseCalendarPeriod): instance of this class starting before
                start of this one.
        """
        raise NotImplementedError(
            "prev is implemented in BaseCalendarPeriod subclasses."
        )

    def contains(self, calendar_period):
        """Check if this calendar period contains another.

        Args:
            calendar_period (BaseCalendarPeriod or Date): calendar period
                or date to check.

        Returns:
            (bool): whether or not calendar period is contained in this.
        """
        raise NotImplementedError(
            "contains is implemented in BaseCalendarPeriod subclasses."
        )

    @property
    def name(self):
        """Get name of class instance to use in serialization.

        Returns:
            (str): name of class instance.
        """
        raise NotImplementedError(
            "name property is implemented in BaseCalendarPeriod subclasses."
        )

    @property
    def full_name(self):
        """Get full name of class.

        Returns:
            (str): full name of class instance. This only differes from
                the name property in cases where name doesn't give
                enough information to fully encode the period.
        """
        return self.name

    def __str__(self):
        """Get string representation of class.

        Returns:
            (str): string representation of class.
        """
        return self.full_name

    def get_time_period_type(self):
        """Get time period type of item.

        This is mostly here just to get around some circular import issues
        with the planned_item class.

        Returns:
            (TimePeriod): the time period.
        """
        return {
            CalendarDay: TimePeriod.DAY,
            CalendarWeek: TimePeriod.WEEK,
            CalendarMonth: TimePeriod.MONTH,
            CalendarYear: TimePeriod.YEAR,
        }.get(type(self))

    def get_planned_items_container(self):
        """Get list that planned items for this period are stored in.

        This is overridden for calendar weeks.

        Returns:
            (list(PlannedItem)): list that planned items are stored in.
        """
        return self._planned_items


class CalendarDay(BaseCalendarPeriod):
    """Class representing a day of calendar data."""
    _SAVE_TYPE = SaveType.FILE
    SCHEDULED_ITEMS_KEY = "scheduled_items"
    PLANNED_ITEMS_KEY = "planned_items"
    PLANNED_WEEK_ITEMS_KEY = "planned_week_items"

    def __init__(self, calendar, date, calendar_month=None):
        """Initialise calendar day object.

        Args:
            calendar (Calendar): calendar root item.
            date (Date): date object.
            calendar_month (CalendarMonth or None): calendar month object.

        Attrs:
            _scheduled_items (list(BaseScheduledItem)): all scheduled item
                instances scheduled on this day.
            _planned_items (list(PlannedItem)): all items planned for this
                day.
            _planned_week_items (list(PlannedWeekItem)): all week items
                planned for the week that starts on this day. These are
                stored here because the week object isn't stored globally
                in the calendar.
            _history (dict): history for this day.
        """
        super(CalendarDay, self).__init__(calendar)
        self._date = date
        self._calendar_month = calendar_month or self.calendar.get_month(
            date.year,
            date.month
        )
        self._scheduled_items = HostedDataList()
        self._planned_items = HostedDataList()
        self._planned_week_items = HostedDataList()
        self._history = calendar.task_root.get_history_for_date(date)

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
    def calendar_month(self):
        """Get calendar month that day is contained in.

        Returns:
            (CalendarMonth): calendar month that day is contained in.
        """
        return self._calendar_month

    @property
    def calendar_year(self):
        """Get calendar year that day is contained in.

        Returns:
            (CalendarYear): calendar year that day is contained in.
        """
        return self._calendar_month._calendar_year

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

    def get_as_one_day_week(self):
        """Get this day as a one-day CalendarWeek object.

        Returns:
            (CalendarWeek): this day represented as a one day week.
        """
        return CalendarWeek(self.calendar, self.date, length=1)

    def iter_scheduled_items(self, filter=None):
        """Iterate through scheduled scheduled items.

        This includes repeat instances as well.

        Args:
            filter (function, BaseFilter or None): filter to apply, if given.

        Yields:
            (ScheduledItem): next scheduled item.
        """
        with self.calendar._repeat_items.apply_filter(filter):
            for repeat_item in self.calendar._repeat_items:
                for item_instance in repeat_item.instances_at_date(self.date):
                    yield item_instance
        with self._scheduled_items.apply_filter(filter):
            for item in self._scheduled_items:
                yield item

    def iter_planned_items(self, filter=None):
        """Iterate through planned day items.

        Args:
            filter (function, BaseFilter or None): filter to apply, if given.

        Yields:
            (PlannedItem): next planned item.
        """
        with self._planned_items.apply_filter(filter):
            for item in self._planned_items:
                yield item

    def get_history_dict(self):
        """Get history dict for this date.

        Structure:
        {
            task_1: {
                status: task_status,
                value: task_value,
                comments: {
                    time_1: comment_1,
                    ...
                }
            },
            ...
        }

        Returns:
            (dict): dict of task history for given date.
        """
        return self._history

    def next(self):
        """Get calendar day immediately after this one.

        Returns:
            (CalendarDay): calendar day after this one.
        """
        return self.calendar.get_day(self.date + TimeDelta(days=1))

    def prev(self):
        """Get calendar day immediately before this one.

        Returns:
            (CalendarDay): calendar day before this one.
        """
        return self.calendar.get_day(self.date - TimeDelta(days=1))

    def contains(self, calendar_period):
        """Check if this calendar period contains another.

        Args:
            calendar_period (BaseCalendarPeriod or Date): calendar period
                or date to check.

        Returns:
            (bool): whether or not calendar period is contained in this.
        """
        # calendar day doesn't contain any other calendar periods
        return False

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = {}
        if self._scheduled_items:
            dict_repr[self.SCHEDULED_ITEMS_KEY] = [
                item.to_dict() for item in self._scheduled_items
            ]
        if self._planned_items:
            dict_repr[self.PLANNED_ITEMS_KEY] = [
                item.to_dict() for item in self._planned_items
            ]
        if self._planned_week_items:
            dict_repr[self.PLANNED_WEEK_ITEMS_KEY] = [
                item.to_dict() for item in self._planned_week_items
            ]
        return dict_repr

    @classmethod
    def from_dict(cls, dict_repr, calendar, calendar_month, day_name):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): root calendar object.
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

        scheduled_items_list = dict_repr.get(cls.SCHEDULED_ITEMS_KEY, [])
        # TODO: [KEY-TRANSFER] delete this after transfer to new key name
        if not scheduled_items_list:
            scheduled_items_list = dict_repr.get("calendar_items", [])
        scheduled_items = [
            ScheduledItem.from_dict(scheduled_item_dict, calendar)
            for scheduled_item_dict in scheduled_items_list
        ]
        calendar_day._scheduled_items.extend(scheduled_items)

        planned_items_list = dict_repr.get(cls.PLANNED_ITEMS_KEY, [])
        planned_items = [
            PlannedItem.from_dict(planned_item_dict, calendar, calendar_day)
            for planned_item_dict in planned_items_list
        ]
        calendar_day._planned_items.extend(planned_items)

        planned_week_items_list = dict_repr.get(cls.PLANNED_WEEK_ITEMS_KEY, [])
        planned_week_items = [
            PlannedItem.from_dict(
                planned_item_dict,
                calendar,
                calendar.get_week_starting_with_date(calendar_day.date)
            )
            for planned_item_dict in planned_week_items_list
        ]
        calendar_day._planned_week_items.extend(planned_week_items)

        return calendar_day


class CalendarWeek(BaseCalendarPeriod):
    """Class representing a week of calendar data.

    Note that unlike the other classes in this module, this one is not fixed -
    it gets generated on the fly when needed to be viewed, and the starting
    day may be changed.

    This means that we can't store any data on it, it essentially just stores
    refs to other calendar periods. Items planned/scheduled for this week
    have to be worked out on the fly from months/days.
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
            length=7):
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

    def __eq__(self, calendar_week):
        """Check if equal to other calendar week.

        Args:
            calendar_week (CalendarWeek): other calendar week to compare to.

        Returns:
            (bool): whether calendar week is equal to this one.
        """
        return (
            isinstance(calendar_week, CalendarWeek)
            and self._start_date == calendar_week._start_date
            and self._length == calendar_week._length
        )

    def __ne__(self, calendar_week):
        """Check if not equal to other calendar week.

        Args:
            calendar_week (CalendarWeek): other calendar week to compare to.

        Returns:
            (bool): whether calendar week is not equal to this one.
        """
        return not self.__eq__(calendar_week)

    def __hash__(self):
        """Hash class instance.

        Returns:
            (int): hash value.
        """
        return hash((self._start_date, self._length))

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

    @property
    def start_day(self):
        """Get start day of calendar week.

        Returns:
            (CalendarDay): start calendar day.
        """
        return self.calendar.get_day(self.start_date)

    @property
    def end_day(self):
        """Get end day of calendar week.

        Returns:
            (CalendarDay): end calendar day.
        """
        return self.calendar.get_day(self.end_date)

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

    @property
    def length(self):
        """Get length of week.

        Returns:
            (int): week length.
        """
        return self._length

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

        Returns:
            (CalendarDay): calendar day at index.
        """
        return list(self.iter_days())[index]

    def iter_planned_items(self, filter=None):
        """Iterate through planned week items.

        If week length isn't 7, we can't treat this as a week so we instead
        iterate through planned day items for each day in week.

        Args:
            filter (function, BaseFilter or None): filter to apply, if given.

        Yields:
            (PlannedItem): next planned item.
        """
        if self.length == 7:
            with self.start_day._planned_week_items.apply_filter(filter):
                for item in self.start_day._planned_week_items:
                    yield item
        else:
            for day in self.iter_days():
                for item in day.iter_planned_items(filter=filter):
                    yield item

    def next(self):
        """Get calendar week starting immediately after this one.

        This returns a standard seven-day week, with starting day immediately
        after the end day of this one.

        Returns
            (CalendarWeek): the calendar week after this one.
        """
        return CalendarWeek(
            self.calendar,
            self.end_date + TimeDelta(days=1),
            length=self._length,
        )

    def prev(self):
        """Get calendar week starting immediately before this one.

        This returns a standard seven-day week, with ending day immediately
        before the start day of this one.

        Returns
            (CalendarWeek): the calendar week before this one.
        """
        return CalendarWeek(
            self.calendar,
            self.start_date - TimeDelta(days=self._length),
            length=self._length,
        )

    def contains(self, calendar_period):
        """Check if this calendar period contains another.

        Args:
            calendar_period (BaseCalendarPeriod or Date): calendar period
                or date to check.

        Returns:
            (bool): whether or not calendar period is contained in this.
        """
        if isinstance(calendar_period, Date):
            return self.contains(self.calendar.get_day(calendar_period))
        if isinstance(calendar_period, CalendarDay):
            return (
                calendar_period.date >= self.start_date
                and calendar_period.date <= self.end_date
            )
        if isinstance(calendar_period, CalendarWeek):
            return (
                calendar_period.start_date >= self.start_date
                and calendar_period.end_date <= self.end_date
                and calendar_period.length < self.length
            )
        return False

    def week_starting_next_day(self):
        """Get calendar week starting one day later than this one.

        Returns:
            (CalendarWeek): calendar week starting a day later than this one.
        """
        return CalendarWeek(
            self.calendar,
            self.start_date + TimeDelta(days=1),
            length=self._length,
        )

    def week_starting_prev_day(self):
        """Get calendar week starting one day earlier than this one.

        Returns:
            (CalendarWeek): calendar week starting a day earlier than this one.
        """
        return CalendarWeek(
            self.calendar,
            self.start_date - TimeDelta(days=1),
            length=self._length,
        )

    def get_planned_items_container(self):
        """Get list that planned items for this period are stored in.

        Returns:
            (list(PlannedItem)): list that planned items are stored in.
        """
        return self.start_day._planned_week_items

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
    _INFO_FILE = "planned_items{0}".format(SerializableFileTypes.INFO)
    _MARKER_FILE = _ORDER_FILE
    _SUBDIR_KEY = "weeks"
    _SUBDIR_CLASS = CalendarWeek
    _SUBDIR_DICT_TYPE = OrderedDict

    WEEKS_KEY = _SUBDIR_KEY
    PLANNED_ITEMS_KEY = "planned_items"

    def __init__(self, calendar, year, month, calendar_year=None):
        """Initialise calendar month object.

        Args:
            calendar (Calendar): calendar root item.
            year (int): the year number.
            month (int): the month number.
            calendar_year (CalendarYear or None): calendar year object.

        Attrs:
            _planned_items (list(PlannedItem)): items planned for this
                month.
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
        self._planned_items = HostedDataList()

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

    @property
    def full_name(self):
        """Get full name of class.

        Returns:
            (str): full name of class instance. This differes from
                the name property in that it includes the year as well.
        """
        return "{0} {1}".format(self.name, self._year)

    @property
    def start_day(self):
        """Get start day of calendar month.

        Returns:
            (CalendarDay): start calendar day.
        """
        return self.calendar.get_day(Date(self._year, self._month, 1))

    @property
    def start_date(self):
        """Get start date of month.

        Returns:
            (Date): start date.
        """
        return self._start_date

    @property
    def end_date(self):
        """Get end date of month.

        Returns:
            (Date): end date.
        """
        return self._start_date + TimeDelta(days=self._length-1)

    @property
    def calendar_year(self):
        """Get calendar year that month is contained in.

        Returns:
            (CalendarYear): calendar year that month is contained in.
        """
        return self._calendar_year

    @property
    def num_days(self):
        """Get number of days in month.

        Returns:
            (int): number of days in month.
        """
        return self._length

    def get_start_week(self, starting_day=0, length=7):
        """Get first week of month.

        Args:
            starting_day (int or str): integer or string representing starting
                day for week.
            length (int): length of week.

        Returns:
            (CalendarWeek): calendar week.
        """
        return self.calendar.get_week_containing_date(
            self.start_day.date,
            starting_day=starting_day,
            length=length,
        )

    def get_calendar_weeks(self, starting_day=0, overspill=False):
        """Get calendar weeks list.

        Args:
            starting_day (int or str): integer or string representing starting
                day for weeks. By default we start weeks on monday.
            overspill (bool): if True, overspill weeks at either side to ensure
                all weeks have length 7.

        Returns:
            (list(CalendarWeek)): list of calendar week objects for this month.
        """
        week_list = []
        if isinstance(starting_day, str):
            starting_day = Date.weekday_int_from_string(starting_day)
        date = self._start_date

        if overspill:
            distance_from_start_day = (date.weekday - starting_day) % 7
            date -= (TimeDelta(days=distance_from_start_day))
            while date <= self._end_date:
                week_list.append(CalendarWeek(self.calendar, date))
                date += TimeDelta(weeks=1)

        else:
            while date <= self._end_date:
                length = 7
                if date.weekday != starting_day:
                    # beginning of month, restrict length til next start day
                    length = (starting_day - date.weekday) % 7
                elif (self._end_date - date).days + 1 < 7:
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

    def iter_planned_items(self, filter=None):
        """Iterate through planned month items.

        Args:
            filter (function, BaseFilter or None): filter to apply, if given.

        Yields:
            (PlannedItem): next planned item.
        """
        with self._planned_items.apply_filter(filter):
            for item in self._planned_items:
                yield item

    def next(self):
        """Get calendar month immediately after this one.

        Returns:
            (CalendarMonth): calendar month after this one.
        """
        new_date = self._start_date + TimeDelta(months=1)
        return self.calendar.get_month(new_date.year, new_date.month)

    def prev(self):
        """Get calendar month immediately before this one.

        Returns:
            (CalendarMonth): calendar month before this one.
        """
        new_date = self._start_date - TimeDelta(months=1)
        return self.calendar.get_month(new_date.year, new_date.month)

    def contains(self, calendar_period):
        """Check if this calendar period contains another.

        Args:
            calendar_period (BaseCalendarPeriod or Date): calendar period
                or Date to check.

        Returns:
            (bool): whether or not calendar period is contained in this.
        """
        if isinstance(calendar_period, Date):
            return self.contains(self.calendar.get_day(calendar_period))
        if isinstance(calendar_period, CalendarDay):
            return (
                calendar_period.date.year == self._year
                and calendar_period.date.month == self._month
            )
        if isinstance(calendar_period, CalendarWeek):
            # count week as contained if there's any crossover
            return (
                self.contains(calendar_period.start_day)
                or self.contains(calendar_period.end_day)
            )
        return False

    def to_dict(self):
        """Serialize class as dict.

        Returns:
            (dict): nested json dict representing calendar object and its
                contained calendar period objects.
        """
        dict_repr = {}
        weeks_dict = OrderedDict()
        for week in self.get_calendar_weeks():
            week_dict = week.to_dict()
            if week_dict:
                weeks_dict[week.name] = week_dict
        if self._planned_items:
            dict_repr[self.PLANNED_ITEMS_KEY] = [
                item.to_dict() for item in self._planned_items
            ]
        if weeks_dict:
            dict_repr[self.WEEKS_KEY] = weeks_dict
        return dict_repr

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
        for week_name, week_dict in dict_repr.get(cls.WEEKS_KEY, {}).items():
            # Note that we don't need to do anything with this, we're just
            # calling the week's from_dict method so it can add the days to
            # the calendar
            CalendarWeek.from_dict(
                week_dict,
                calendar,
                calendar_month,
                week_name,
            )
        calendar_month._planned_items.extend([
            PlannedItem.from_dict(dict_, calendar, calendar_month)
            for dict_ in dict_repr.get(cls.PLANNED_ITEMS_KEY, [])
        ])
        return calendar_month


class CalendarYear(BaseCalendarPeriod):
    """Class representing a year of calendar data."""
    _SAVE_TYPE = SaveType.DIRECTORY
    _ORDER_FILE = "year{0}".format(SerializableFileTypes.ORDER)
    _INFO_FILE = "planned_items{0}".format(SerializableFileTypes.INFO)
    _MARKER_FILE = _ORDER_FILE
    _SUBDIR_KEY = "months"
    _SUBDIR_CLASS = CalendarMonth
    _SUBDIR_DICT_TYPE = OrderedDict

    MONTHS_KEY = _SUBDIR_KEY
    PLANNED_ITEMS_KEY = "planned_items"

    def __init__(self, calendar, year):
        """Initialise calendar year object.

        Args:
            calendar_obj (Calendar): the calendar parent item.
            year (int): the year number.

        Attrs:
            _planned_items (list(PlannedItem)): items planned for this
                month.
        """
        super(CalendarYear, self).__init__(calendar)
        self._year = year
        self._length = 12
        self.__calendar_months = None
        self._planned_items = HostedDataList()

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

    @property
    def year(self):
        """Get year number.

        Returns:
            (int): the year.
        """
        return self._year

    @property
    def start_day(self):
        """Get start day of calendar year.

        Returns:
            (CalendarDay): start calendar day.
        """
        return self.calendar.get_day(Date(self._year, 1, 1))

    @property
    def start_date(self):
        """Get start date of year.

        Returns:
            (Date): start date.
        """
        return self.start_day.date

    @property
    def end_date(self):
        """Get end date of year.

        Returns:
            (Date): end date.
        """
        return self.calendar.get_day(Date(self._year, 12, 31)).date

    def get_start_week(self, starting_day=0, length=7):
        """Get first week of year.

        Args:
            starting_day (int or str): integer or string representing starting
                day for week.
            length (int): length of week.

        Returns:
            (CalendarWeek): calendar week.
        """
        return self.calendar.get_week_containing_date(
            self.start_day.date,
            starting_day=starting_day,
            length=length,
        )

    def iter_months(self):
        """Iterate through months in class.

        Yields:
            (CalendarMonth): next calendar month.
        """
        for month in self._calendar_months.values():
            yield month

    def iter_planned_items(self, filter=None):
        """Iterate through planned year items.

        Args:
            filter (function, BaseFilter or None): filter to apply, if given.

        Yields:
            (PlannedItem): next planned item.
        """
        with self._planned_items.apply_filter(filter):
            for item in self._planned_items:
                yield item

    def next(self):
        """Get calendar year immediately after this one.

        Returns:
            (CalendarYear): calendar year after this one.
        """
        return self.calendar.get_year(self._year + 1)

    def prev(self):
        """Get calendar year immediately before this one.

        Returns:
            (CalendarYear): calendar year before this one.
        """
        return self.calendar.get_year(self._year - 1)

    def contains(self, calendar_period):
        """Check if this calendar period contains another.

        Args:
            calendar_period (BaseCalendarPeriod or Date): calendar period
                or Date to check.

        Returns:
            (bool): whether or not calendar period is contained in this.
        """
        if isinstance(calendar_period, Date):
            return self.contains(self.calendar.get_day(calendar_period))
        if isinstance(calendar_period, CalendarDay):
            return calendar_period.date.year == self._year
        if isinstance(calendar_period, CalendarWeek):
            # count week as contained if there's any crossover
            return (
                self.contains(calendar_period.start_day)
                or self.contains(calendar_period.end_day)
            )
        if isinstance(calendar_period, CalendarMonth):
            return calendar_period._year == self._year
        return False

    def to_dict(self):
        """Serialize class as dict.

        Returns:
            (dict): nested json dict representing calendar year object and its
                contained calendar month objects.
        """
        dict_repr = {}
        months_dict = OrderedDict()
        for month in self._calendar_months.values():
            month_dict = month.to_dict()
            if month_dict:
                months_dict[month.name] = month_dict
        if months_dict:
            dict_repr[self.MONTHS_KEY] = months_dict
        if self._planned_items:
            dict_repr[self.PLANNED_ITEMS_KEY] = [
                item.to_dict() for item in self._planned_items
            ]
        return dict_repr

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
        calendar_year._planned_items.extend([
            PlannedItem.from_dict(dict_, calendar, calendar_year)
            for dict_ in dict_repr.get(cls.PLANNED_ITEMS_KEY, [])
        ])
        return calendar_year
