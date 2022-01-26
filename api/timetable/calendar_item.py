"""Calendar item class."""

from collections import OrderedDict

from scheduler.api.common.date_time import Date, DateTime, Time, TimeDelta
from scheduler.api.common.serializable import NestedSerializable, SaveType
from scheduler.api.tree.task import Task
from scheduler.api.tree.task_category import TaskCategory


#TODO standardize exceptions
class CalendarItemError(Exception):
    """Generic exception for calendar item errors."""


class CalendarItemType():
    """Struct defining types of calendar items."""
    TASK = "task"
    EVENT = "event"


class CalendarItemRepeatPattern(object):
    """Class to determine the dates of a repeating calendar item."""

    DAY_REPEAT = "day_repeat"
    WEEK_REPEAT = "week_repeat"
    MONTH_REPEAT = "month_repeat"
    YEAR_REPEAT = "year_repeat"

    def __init__(self, inital_date_pattern, timedelta_gap, repeat_type=None):
        """Initialise class.

        Args:
            initial_date_pattern (list(Date)): list of first dates of repeating
                item.
            timedelta_gap (TimeDelta): gap of time after first date before
                pattern repeats.
            repeat_type (str or None): type of repeating used.
        """
        self._initial_date_pattern = inital_date_pattern
        if inital_date_pattern[0] + timedelta_gap <= inital_date_pattern[-1]:
            raise CalendarItemError(
                "CalendarItemRepeat timedelta_gap is too small for given range"
            )
        self.start_date = inital_date_pattern[0]
        self._pattern_size = len(inital_date_pattern)
        self._gap = timedelta_gap
        self._gap_multiplier = 1
        self._dates = inital_date_pattern
        self.repeat_type = repeat_type or self.DAY_REPEAT

    @property
    def initial_dates(self):
        """Get dates of initial repeat pattern.

        Returns:
            (list(Date)): list of days of initial pattern.
        """
        return self._initial_date_pattern

    @classmethod
    def day_repeat(cls, inital_date_pattern, day_gap):
        """Initialise class as pattern of dates with gap of days in between.

        Args:
            initial_date_pattern (list(Date)): list of first dates of repeating
                item.
            day_gap (int): number of days before pattern repeats.

        Returns:
            (CalendarItemRepeat): class instance.
        """
        return cls(
            inital_date_pattern,
            TimeDelta(days=day_gap),
            cls.DAY_REPEAT,
        )

    @classmethod
    def week_repeat(cls, starting_day, weekdays, week_gap=1):
        """Initialise class as set of weekdays with week gap in between.

        Args:
            starting_day (Date): first date of calendar item.
            weekdays (list(str)): list of weekdays that this will
                repeat on.
            week_gap (int): number of weeks before repeating.

        Returns:
            (CalendarItemRepeat): class instance.
        """
        weekdays = [
            Date.weekday_int_from_string(weekday) for weekday in weekdays
        ]
        def days_from_start(weekday_int):
            return (weekday_int - starting_day.weekday) % Date.NUM_WEEKDAYS
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
        )

    @classmethod
    def month_repeat(cls, inital_date_pattern, month_gap=1):
        """Initialise class as pattern of dates with month gap in between.

        Args:
            initial_date_pattern (list(Date)): list of first dates of repeating
                item.
            month_gap (int): number of months before pattern repeats.

        Returns:
            (CalendarItemRepeat): class instance.
        """
        return cls(
            inital_date_pattern,
            TimeDelta(months=month_gap),
            cls.MONTH_REPEAT,
        )

    @classmethod
    def year_repeat(cls, inital_date_pattern, year_gap=1):
        """Initialise class as pattern of dates with year gap in between.

        Args:
            initial_date_pattern (list(Date)): list of first dates of repeating
                item.
            year_gap (int): number of years before pattern repeats.

        Returns:
            (CalendarItemRepeat): class instance.
        """
        return cls(
            inital_date_pattern,
            TimeDelta(years=year_gap),
            cls.YEAR_REPEAT,
        )

    def _update_to_date(self, date):
        """Update internal list of dates to include all before given date.

        Args:
            date (Date): date to updaet to.
        """
        while self._dates[-1] < date:
            for initial_date in self._initial_date_pattern:
                self._dates.append(
                    initial_date + self._gap * self._gap_multiplier
                )
            self._gap_multiplier += 1

    def check_date(self, date):
        """Check if the repeating item will fall on the given date.

        Args:
            date (Date): date to check.

        Returns:
            (bool): whether or not item falls on given date.
        """
        self._update_to_date(date)
        return date in self._dates

    def dates_between(self, start_date, end_date):
        """Get dates in repeating pattern between the two given dates.

        Args:
            start_date (Date): start date. This is exclusive (ie. not included
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
            elif start_date < date <= end_date:
                yield date
            else:
                break


class BaseCalendarItem(NestedSerializable):
    """Base calendar item class representing a scheduled task or event."""
    _SAVE_TYPE = SaveType.NESTED

    START_AND_END_TYPE = Time
    START_KEY = "start"
    END_KEY = "end"
    TYPE_KEY = "type"
    TREE_ITEM_KEY = "tree_item"
    NAME_KEY = "name"
    CATEGORY_KEY = "category"
    BACKGROUND_KEY = "background"

    def __init__(
            self,
            calendar,
            start_time,
            end_time,
            item_type=None,
            tree_item=None,
            event_category=None,
            event_name=None,
            is_background=False):
        """Initialise item.

        Args:
            calendar (Calendar): calendar class instance.
            start_time (Time): start time.
            end_time (Time): end time.
            item_type (CalendarItemType or None): type of scheduled item.
            tree_item (BaseTreeItem or None): tree item representing task,
                if item_type is task.
            event_category (str or None): name to be used for category of item,
                if item_type is event.
            event_name (str or None): name of event, if item_type is event.
            is_background (bool): if True, this is a 'background' item, ie. a
                higher level task or event that subevents or subtasks can be
                overlayed on.
        """
        self._calendar = calendar
        self._task_root = calendar.task_root
        self._start_time = start_time
        self._end_time = end_time
        self._type = item_type or CalendarItemType.TASK
        self._tree_item = tree_item
        self._event_category = event_category or ""
        self._event_name = event_name or ""
        self._is_background = is_background

    @property
    def start_time(self):
        """Get start time.

        Returns:
            (Time): start time.
        """
        return self._start_time

    @property
    def end_time(self):
        """Get end time.

        Returns:
            (Time): end time.
        """
        return self._end_time

    @property
    def type(self):
        """Get type of calendar item.

        Returns:
            (CalendarItemType): item type.
        """
        return self._type

    @property
    def tree_item(self):
        """Get tree item representing task.

        Returns:
            (BaseTreeItem or None): task or task category tree item, if one
                exists.
        """
        return self._tree_item

    @property
    def category(self):
        """Get item category name.

        Returns:
            (str): name to use for item category.
        """
        if self._type == CalendarItemType.TASK:
            # TODO: this is dodgy, task_category shouldn't 
            # have a top_level_task method, change this in refactor
            if isinstance(self._tree_item, (Task, TaskCategory)):
                # and there should be a better system in general for dealing
                # with the case where category==name
                if self._tree_item.top_level_task() != self._tree_item:
                    return self._tree_item.top_level_task().name
            return ""
        else:
            return self._event_category

    @property
    def name(self):
        """Get item name.

        Returns:
            (str): name to use for item.
        """
        if self._type == CalendarItemType.TASK:
            if self._tree_item:
                return self._tree_item.name
            return ""
        else:
            return self._event_name

    @property
    def is_background(self):
        """Return whether or not this is a background item.

        Returns:
            (bool): whether or not this is a background item.
        """
        return self._is_background

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = {
            self.START_KEY: self._start_time.string(),
            self.END_KEY: self._end_time.string(),
            self.TYPE_KEY: self._type,
        }
        if self.type == CalendarItemType.TASK and self._tree_item:
            dict_repr[self.TREE_ITEM_KEY] = self._tree_item.path
        else:
            dict_repr[self.CATEGORY_KEY] = self._event_category
            dict_repr[self.NAME_KEY] = self._event_name
        if self._is_background:
            dict_repr[self.BACKGROUND_KEY] = self._is_background
        return dict_repr

    @classmethod
    def from_dict(cls, dict_repr, calendar, *args):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): root calendar object.
            args (list): additional args to pass to __init__.

        Returns:
            (BaseCalendarItem or None): calendar item, if can be initialised.
        """
        # TODO: create deserialize method in serializable class that works
        # out how to deserialize based on type.
        start = cls.START_AND_END_TYPE.from_string(
            dict_repr.get(cls.START_KEY)
        )
        end = cls.START_AND_END_TYPE.from_string(
            dict_repr.get(cls.END_KEY)
        )
        type_ = dict_repr.get(cls.TYPE_KEY)
        if not (start and end and type_):
            return None
        tree_item = calendar.task_root.get_item_at_path(
            dict_repr.get(cls.TREE_ITEM_KEY)
        )
        category = dict_repr.get(cls.CATEGORY_KEY)
        name = dict_repr.get(cls.NAME_KEY)
        is_background = dict_repr.get(cls.BACKGROUND_KEY, False)

        return cls(
            calendar,
            start,
            end,
            type_,
            tree_item,
            category,
            name,
            is_background,
        )


class CalendarItem(BaseCalendarItem):
    """Calendar item class representing a scheduled task or event.

    This is same as base class but includes a date as well, and so the
    start and end keys of the dictionary representation are DateTime
    objects rather than date ones.
    """
    START_AND_END_TYPE = DateTime

    def __init__(
            self,
            calendar,
            start_datetime,
            end_datetime,
            item_type=None,
            tree_item=None,
            event_category=None,
            event_name=None,
            is_background=False):
        """Initialise item.

        Args:
            calendar (Calendar): calendar class instance.
            start_datetime (DateTime): start date time.
            end_datetime (DateTime): end date time.
            item_type (CalendarItemType or None): type of scheduled item.
            tree_item (BaseTreeItem or None): tree item representing task,
                if item_type is task.
            event_category (str or None): name to be used for category of item,
                if item_type is event.
            event_name (str or None): name of event, if item_type is event.
            is_background (bool): if True, this is a 'background' item, ie. a
                higher level task or event that subevents or subtasks can be
                overlayed on.
        """
        super(CalendarItem, self).__init__(
            calendar,
            start_datetime.time(),
            end_datetime.time(),
            item_type,
            tree_item,
            event_category,
            event_name,
            is_background
        )
        self._date = start_datetime.date()

    @property
    def _start_datetime(self):
        """Get start datetime.

        Returns:
            (DateTime): start datetime.
        """
        return DateTime.from_date_and_time(self._date, self._start_time)

    @_start_datetime.setter
    def _start_datetime(self, value):
        """Setter for start datettime.

        This allows us to update the class either by Date and Time or DateTime.

        Args:
            value (DateTime): new datetime value.
        """
        self._date = value.date()
        self._start_time = value.time()

    @property
    def _end_datetime(self):
        """Get end datetime.

        Returns:
            (Time): end datetime.
        """
        return DateTime.from_date_and_time(self._date, self._end_time)

    @_end_datetime.setter
    def _end_datetime(self, value):
        """Setter for end datettime.

        This allows us to update the class either by Date and Time or DateTime.

        Args:
            value (DateTime): new datetime value.
        """
        # currently event can only be one day
        self._date = value.date()
        self._end_time = value.time()

    # TODO: for now this assumes that the event is only on one day
    @property
    def date(self):
        """Get date of item.

        Returns:
            (Date): date.
        """
        return self._date


class RepeatCalendarItem(BaseCalendarItem):
    """Class for repeating calendar items."""
    OVERRIDDEN_INSTANCES_KEY = "overridden_instances"

    def __init__(
            self,
            calendar,
            start_time,
            end_time,
            repeat_pattern,
            item_type=None,
            tree_item=None,
            event_category=None,
            event_name=None,
            is_background=False):
        """Initialise item.

        Args:
            calendar (Calendar): calendar class instance.
            start_time (Time): start time.
            end_time (Time): end time.
            repeat_pattern (CalendarItemRepeatPattern): repeat pattern object,
                describing what days this item repeats on.
            item_type (CalendarItemType or None): type of scheduled item.
            tree_item (BaseTreeItem or None): tree item representing task,
                if item_type is task.
            event_category (str or None): name to be used for category of item,
                if item_type is event.
            event_name (str or None): name of event, if item_type is event.
            is_background (bool): if True, this is a 'background' item, ie. a
                higher level task or event that subevents or subtasks can be
                overlayed on.

        Attributes:
            _instances (dict(Date, RepeatCalendarItemInstance)): dictionary of
                instances of this repeat item, keyed by the date they're
                scheduled for originally. If the item has it's date overridden,
                the date key remains unchanged.
            _overridden_instances (dict(Date, RepeatCalendarItemInstance)):
                dictionary of all instances that have overrides on their time/
                date. These are the only ones that need to be saved during
                serialization.
        """
        super(RepeatCalendarItem, self).__init__(
            calendar,
            start_time,
            end_time,
            item_type,
            tree_item,
            event_category,
            event_name,
            is_background
        )
        self._repeat_pattern = repeat_pattern
        self._instances = OrderedDict()
        self._overridden_instances = {}

    @property
    def _start_date(self):
        """Get start date of repeat pattern.

        Returns:
            (Date): date of first instance of repeat calendar item.
        """
        return self._repeat_pattern.start_date

    @property
    def repeat_pattern(self):
        """Get repeat pattern of item.

        Returns:
            (CalendarItemRepeatPattern): repeat pattern.
        """
        return self._repeat_pattern

    def instances_at_date(self, date):
        """Get instance at given date, if one exits.

        Args:
            date (Date): date to check.

        Returns:
            (list(RepeatCalendarItemInstance): list of all repeat calendar item
                instances that exist at the given date. Note that this will
                include any items that are overridden to the current date, and
                will not include items originally scheduled for this date that
                have been moved.
        """
        latest_date = self._start_date
        if self._instances:
            latest_date = self._instances.keys()[-1]
        for _date in self._repeat_pattern.dates_between(latest_date, date):
            if _date in self._overridden_instances.keys():
                self._instances[_date] = self._overridden_instances[_date]
            else:
                self._instances[_date] = RepeatCalendarItemInstance(
                    self,
                    _date
                )

        instances_at_date = []
        scheduled_instance = self._instances.get(date, None)
        if scheduled_instance and scheduled_instance.date == date:
            instances_at_date.append(self._instances[date])
        for instance in self._overridden_instances.values():
            if instance.date == date and instance != scheduled_instance:
                instances_at_date.append(instance)
        return instances_at_date

    def _clean_overrides(self):
        """Remove overrides that no longer apply.

        This should be called after the repeat pattern or times are changed,
        to remove ghost overrides.
        """
        for scheduled_date, instance in self._overridden_instances.items():
            if (not self.instance_at_date(scheduled_date)
                    or not instance.is_override()):
                del self._overridden_instances[scheduled_date]

    def _clear_instances(self):
        """Clear instances list so they can be recalculated."""
        self._instances = OrderedDict()

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = super(CalendarItem, self).to_dict()
        overrides_dict = OrderedDict()
        dict_repr[self.OVERRIDDEN_INSTANCES_KEY] = overrides_dict
        for original_date, instance in self._overridden_instances.items():
            if instance.is_override():
                overrides_dict[original_date.string()] = instance.to_dict()
        return dict_repr

    @classmethod
    def from_dict(cls, dict_repr, calendar):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): root calendar object.

        Returns:
            (BaseCalendarItem or None): calendar item, if can be initialised.
        """
        repeat_item = super(RepeatCalendarItem, cls).from_dict(
            dict_repr,
            calendar
        )
        overrides = dict_repr.get(cls.OVERRIDDEN_INSTANCES_KEY, {})
        for date_str, instance_dict in overrides.items():
            date = Date.from_string(date_str)
            repeat_item._overridden_instances[date] = (
                RepeatCalendarItemInstance.from_dict(
                    instance_dict,
                    repeat_item,
                    date
                )
            )
        return repeat_item


# TODO: I really don't like the amount of repetition between the three CalendarItem
# classes - but couldn't think of a satisfactory way to share all the relevant info
# maybe not worth doing in the end, but I feel like there could be a neater way of
# doing all this.
class RepeatCalendarItemInstance(BaseCalendarItem):
    """Instance of a repeated calendar item.

    This has similar properties to CalendarItem, but inherits all of them from
    the RepeatCalendarItem object it uses as a template.

    Note that currently although it inherits from BaseCalendarItem, it actually
    reimplements all its methods.
    """
    OVERRIDE_START_KEY = "start_override"
    OVERRIDE_END_KEY = "end_override"

    def __init__(
            self,
            repeat_calendar_item,
            scheduled_date,
            override_start_datetime=None,
            override_end_datetime=None):
        """Initialise class.

        Args:
            repeat_calendar_item (RepeatCalendarItem): the repeat calendar item
                that this is an instance of.
            scheduled_date (Date): date this instance is scheduled for.
            override_start_datetime (DateTime or None): start date time to
                override from repeat_item template.
            override_end_datetime (DateTime): start date time to override from
                repeat_item template.
        """
        self._repeat_calendar_item = repeat_calendar_item
        self._scheduled_date = scheduled_date
        self._override_start_datetime = override_start_datetime
        self._override_end_datetime = override_end_datetime

    @property
    def start_time(self):
        """Get start time.

        Returns:
            (Time): start time.
        """
        if self._override_start_datetime:
            return self._override_start_datetime.time()
        return self._repeat_calendar_item.start_time

    @property
    def scheduled_start_time(self):
        """Get scheduled start time.

        Returns:
            (Time): scheduled start time.
        """
        return self._repeat_calendar_item.start_time

    @property
    def scheduled_end_time(self):
        """Get scheduled end time.

        Returns:
            (Time): scheduled end time.
        """
        return self._repeat_calendar_item.end_time

    @property
    def end_time(self):
        """Get end time.

        Returns:
            (Time): end time.
        """
        if self._override_end_datetime:
            return self._override_end_datetime.time()
        return self._repeat_calendar_item.end_time

    @property
    def scheduled_date(self):
        """Get date that item is scheduled for (before overrides).

        Returns:
            (Date): scheduled date.
        """
        return self.scheduled_date

    @property
    def date(self):
        """Get date item is actually at.

        Returns:
            (Date): actual date.
        """
        if self._override_start_datetime:
            return self._override_start_datetime.date()
        return self.scheduled_date

    @property
    def type(self):
        """Get type of calendar item.

        Returns:
            (CalendarItemType): item type.
        """
        return self._repeat_calendar_item.type

    @property
    def tree_item(self):
        """Get tree item representing task.

        Returns:
            (BaseTreeItem or None): task or task category tree item, if one
                exists.
        """
        return self._repeat_calendar_item.tree_item

    @property
    def category(self):
        """Get item category name.

        Returns:
            (str): name to use for item category.
        """
        return self._repeat_calendar_item.category

    @property
    def name(self):
        """Get item name.

        Returns:
            (str): name to use for item.
        """
        return self._repeat_calendar_item.name

    @property
    def is_background(self):
        """Return whether or not this is a background item.

        Returns:
            (bool): whether or not this is a background item.
        """
        return self._repeat_calendar_item._is_background

    def is_override(self):
        """Check whether the given instance overrides the repeat template.

        Returns:
            (bool): whether this instance is an override.
        """
        override_start_datetime = self._override_start_datetime
        override_end_datetime = self._override_end_datetime
        if override_start_datetime is not None:
            if override_start_datetime.date() != self.scheduled_date:
                return True
            if override_start_datetime.time() != self.scheduled_start_time:
                return True
        if override_end_datetime is not None:
            if override_end_datetime.date() != self.scheduled_date:
                return True
            if override_end_datetime.time() != self.scheduled_end_time:
                return True
        return False

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = {
            self.SCHEDULED_DATE_KEY: self._scheduled_date.string()
        }
        if self._override_start_datetime:
            dict_repr[self.OVERRIDE_START_KEY] = (
                self._override_start_datetime.string()
            )
        if self._override_end_datetime:
            dict_repr[self.OVERRIDE_END_KEY] = (
                self._override_end_datetime.string()
            )
        return dict_repr

    @classmethod
    def from_dict(cls, dict_repr, repeat_calendar_item, scheduled_date):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            repeat_calendar_item (RepeatCalendarItem): the repeat calendar item
                that this is an instance of.
            scheduled_date (Date): original scheduled date of item.

        Returns:
            (BaseCalendarItem or None): calendar item, if can be initialised.
        """
        return cls(
            repeat_calendar_item,
            scheduled_date,
            dict_repr.get(cls.OVERRIDE_START_KEY),
            dict_repr.get(cls.OVERRIDE_END_KEY)
        )
