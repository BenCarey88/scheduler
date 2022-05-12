"""Calendar item class."""

from collections import OrderedDict

from scheduler.api.common.date_time import (
    Date,
    DateTime,
    DateTimeError,
    Time,
    TimeDelta,
)
from scheduler.api.common.object_wrappers import (
    Hosted,
    MutableAttribute,
    MutableHostedAttribute,
)
from scheduler.api.serialization import item_registry
from scheduler.api.serialization.serializable import (
    NestedSerializable,
    SaveType,
)
from scheduler.api.tree.task import Task
from scheduler.api.tree.task_category import TaskCategory


#TODO standardize exceptions
class CalendarItemError(Exception):
    """Generic exception for calendar item errors."""


class CalendarItemType():
    """Struct defining types of calendar items."""
    TASK = "task"
    EVENT = "event"


class CalendarItemRepeatPattern(NestedSerializable):
    """Class to determine the dates of a repeating calendar item."""
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
        super(CalendarItemRepeatPattern, self).__init__()
        self._initial_date_pattern = inital_date_pattern
        if inital_date_pattern[0] + timedelta_gap <= inital_date_pattern[-1]:
            raise CalendarItemError(
                "CalendarItemRepeat timedelta_gap is too small for given range"
            )
        self.start_date = inital_date_pattern[0]
        self._pattern_size = len(inital_date_pattern)
        self._gap = timedelta_gap
        self._gap_multiplier = 1
        self._dates = [date for date in inital_date_pattern]
        self._repeat_type = repeat_type or self.DAY_REPEAT
        self._end_date = end_date

    @property
    def initial_dates(self):
        """Get dates of initial repeat pattern.

        Returns:
            (list(Date)): list of days of initial pattern.
        """
        return self._initial_date_pattern

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
            (CalendarItemRepeat): class instance.
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
            starting_day (Date): first date of calendar item.
            weekdays (list(str)): list of weekdays that this will
                repeat on.
            week_gap (int): number of weeks before repeating.
            end_date (Date or None): end date, if one exists.

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
            (CalendarItemRepeat): class instance.
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
            (CalendarItemRepeat): class instance.
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
            date (Date): date to updaet to.
        """
        if self._end_date is not None:
            date = min(date, self._end_date)
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
            elif start_date <= date <= end_date:
                yield date
            else:
                break

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
                int(self._gap.days / Date.NUM_WEEKDAYS)
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
            (CalendarItemRepeatPattern or None): repeat pattern, if can be
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


class BaseCalendarItem(Hosted, NestedSerializable):
    """Base calendar item class representing a scheduled task or event.

    This class doesn't include any datetime information as the way this data
    is used and serialized varies depending on whether the item repeats or not,
    so this is implemented in the subclasses.
    """
    _SAVE_TYPE = SaveType.NESTED

    TYPE_KEY = "type"
    TREE_ITEM_KEY = "tree_item"
    NAME_KEY = "name"
    CATEGORY_KEY = "category"
    BACKGROUND_KEY = "background"
    ID_KEY = "id"

    def __init__(
            self,
            calendar,
            start_time=None,
            end_time=None,
            date=None,
            repeat_pattern=None,
            item_type=None,
            tree_item=None,
            event_category=None,
            event_name=None,
            is_background=None,
            template_item=None):
        """Initialise item.

        Args:
            calendar (Calendar): calendar class instance.
            start_time (Time or None): time item starts at.
            end_time (Time or None): time item ends at.
            date (Date or None): date item starts at.
            repeat_pattern (RepeatPattern or None): repeat pattern of item.
                This is only used for repeat calendar items, but can be stored
                in standard calendar items so it's saved when converting to a
                repeat one.
            item_type (CalendarItemType or None): type of scheduled item.
            tree_item (BaseTreeItem or None): tree item representing task,
                if item_type is task.
            event_category (str or None): name to be used for category of item,
                if item_type is event.
            event_name (str or None): name of event, if item_type is event.
            is_background (bool): if True, this is a 'background' item, ie. a
                higher level task or event that subevents or subtasks can be
                overlayed on.
            template_item (BaseCalendarItem or None): template item to inherit
                properties from, if they're not overridden. This is used by
                RepeatCalendarItemInstances.
        """
        super(BaseCalendarItem, self).__init__()
        self._calendar = calendar
        self._task_root = calendar.task_root
        self._template_item = template_item
        if template_item is None:
            # if we can't inherit from a template item, set default values
            item_type = item_type or CalendarItemType.TASK
            event_category = event_category or ""
            event_name = event_name or ""
            is_background = is_background or False

        self._start_time = MutableAttribute(start_time, "start_time")
        self._end_time = MutableAttribute(end_time, "end_time")
        self._date = MutableAttribute(date, "date")
        self._repeat_pattern = MutableAttribute(
            repeat_pattern,
            "repeat_pattern"
        )
        self._type = MutableAttribute(item_type, "type")
        self._tree_item = MutableHostedAttribute(tree_item, "tree_item")
        self._event_category = MutableAttribute(
            event_category,
            "event_category"
        )
        self._event_name = MutableAttribute(event_name, "event_name")
        self._is_background = MutableAttribute(is_background, "is_background")
        self._id = None

    class _Decorators(object):
        """Internal decorators class."""
        @staticmethod
        def template_item_decorator(property_func):
            """Decorator for property method.

            Args:
                property_func (function): the property function to decorate.

            Returns:
                (function): the decorated function. This returns the equivalent
                    property of the template item, if one exists and the
                    property of this instance would be None. This is for
                    convenience to avoid too much unnecessary repetition of
                    definitions in the RepeatCalendarItemInstance class. It
                    means that RepeatCalendarItemInstances can rely on their
                    template class for their attributes unless overridden.
            """
            def decorated_func(self):
                property_value = property_func(self)
                if self._template_item is not None and property_value is None:
                    return property_func(self._template_item)
                return property_value
            return decorated_func

    _template_item_decorator = _Decorators.template_item_decorator

    @property
    def calendar(self):
        """Get calendar object.

        Returns:
            (Calendar): the calendar object.
        """
        return self._calendar

    @property
    @_template_item_decorator
    def start_time(self):
        """Get start time of item.

        Returns:
            (Time): time item starts at.
        """
        return self._start_time.value

    @property
    @_template_item_decorator
    def end_time(self):
        """Get end time of item.

        Returns:
            (Time): time item ends at.
        """
        return self._end_time.value

    @property
    def date(self):
        """Get date of item.

        Returns:
            (Date): date item starts at.
        """
        return self._date.value

    @property
    def start_datetime(self):
        """Get start datetime of item.
        
        Returns:
            (Date or None): datetime item starts at.
        """
        if self.date:
            return DateTime.from_date_and_time(self.date, self.start_time)
        return None

    @property
    def end_datetime(self):
        """Get end datetime of item.
        
        Returns:
            (Date or None): datetime item end at. For repeat items, this is the
                end datetime of the first repeat.
        """
        if self.date:
            return DateTime.from_date_and_time(self.date, self.start_time)
        return None

    @property
    @_template_item_decorator
    def repeat_pattern(self):
        """Get repeat pattern of item.

        Returns:
            (RepeatPattern): item repeat pattern (only used by repeat items).
        """
        return self._repeat_pattern.value

    @property
    @_template_item_decorator
    def type(self):
        """Get type of calendar item.

        Returns:
            (CalendarItemType): item type.
        """
        return self._type.value

    @property
    @_template_item_decorator
    def tree_item(self):
        """Get tree item representing task.

        Returns:
            (BaseTreeItem or None): task or task category tree item, if one
                exists.
        """
        return self._tree_item.value

    @property
    @_template_item_decorator
    def category(self):
        """Get item category name.

        Returns:
            (str): name to use for item category.
        """
        if self.type == CalendarItemType.TASK:
            # TODO: this is dodgy, task_category shouldn't 
            # have a top_level_task method, change this in refactor
            if isinstance(self.tree_item, (Task, TaskCategory)):
                # and there should be a better system in general for dealing
                # with the case where category==name
                if self.tree_item.top_level_task() != self.tree_item:
                    return self.tree_item.top_level_task().name
            return ""
        else:
            return self._event_category.value

    @property
    @_template_item_decorator
    def name(self):
        """Get item name.

        Returns:
            (str): name to use for item.
        """
        if self.type == CalendarItemType.TASK:
            if self.tree_item:
                return self.tree_item.name
            return ""
        else:
            return self._event_name.value

    @property
    @_template_item_decorator
    def is_background(self):
        """Return whether or not this is a background item.

        Returns:
            (bool): whether or not this is a background item.
        """
        return self._is_background.value

    def datetime_string(self):
        """Get string representing start and end date/time of item.

        Returns:
            (str): string representing date/time of item.
        """
        raise NotImplementedError(
            "datetime_string is implemented in calendar item subclasses."
        )

    def get_item_container(self, datetime=None):
        """Get the list that this item should be contained in.

        Args:
            datetime (DateTime or None): datetime to query at. If not given, use
                the item's internal start date time.

        Returns:
            (list): list that calendar item should be contained in.
        """
        raise NotImplementedError(
            "get_item_container is implemented in calendar item subclasses."
        )

    def get_id(self):
        """Generate unique id for object.

        This should be used only during the serialization process, so that
        the data used for the id string is up to date. Note that once this
        is run the id string is fixed, allowing it to be referenced by other
        classes during serialization (see the item_registry module for
        more information on how this is done).

        Returns:
            (str): unique id.
        """
        if self._id is None:
            self._id = item_registry.generate_unique_id(
                "{0} {1}".format(self.name, self.datetime_string())
            )
        return self._id

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = {}
        if self._type:
            dict_repr[self.TYPE_KEY] = self._type.value
        if self.type == CalendarItemType.TASK:
            if self._tree_item:
                dict_repr[self.TREE_ITEM_KEY] = self._tree_item.value.path
        else:
            if self._event_category:
                dict_repr[self.CATEGORY_KEY] = self._event_category.value
            if self._event_name:
                dict_repr[self.NAME_KEY] = self._event_name.value
        if self._is_background:
            dict_repr[self.BACKGROUND_KEY] = self._is_background.value
        dict_repr[self.ID_KEY] = self._id
        return dict_repr

    @classmethod
    def from_dict(cls, dict_repr, calendar, *date_args):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): root calendar object.
            args (list): additional args to pass to __init__. These will all
                be to do with date and time, and get passed to the start of
                the __init__ function.

        Returns:
            (BaseCalendarItem or None): calendar item, if can be initialised.
        """
        item_type = dict_repr.get(cls.TYPE_KEY)
        tree_item = calendar.task_root.get_item_at_path(
            dict_repr.get(cls.TREE_ITEM_KEY)
        )
        category = dict_repr.get(cls.CATEGORY_KEY)
        name = dict_repr.get(cls.NAME_KEY)
        is_background = dict_repr.get(cls.BACKGROUND_KEY, False)

        calendar_item = cls(
            calendar,
            *date_args,
            item_type=item_type,
            tree_item=tree_item,
            event_category=category,
            event_name=name,
            is_background=is_background,
        )
        id = dict_repr.get(cls.ID_KEY, None)
        if id is not None:
            item_registry.register_item(id, calendar_item)
        return calendar_item


class CalendarItem(BaseCalendarItem):
    """Calendar item class representing a scheduled task or event.

    This uses DateTime values to define the start and end date and time of
    the item.
    """
    START_KEY = "start"
    END_KEY = "end"
    START_DATETIME_KEY = "start_datetime"
    END_DATETIME_KEY = "end_datetime"

    def __init__(
            self,
            calendar,
            start_time,
            end_time,
            date,
            item_type=None,
            tree_item=None,
            event_category=None,
            event_name=None,
            is_background=None,
            repeat_pattern=None):
        """Initialise item.

        Args:
            calendar (Calendar): calendar class instance.
            start_datetime (Time): start time.
            end_datetime (Time): end time.
            date (Date): date of item.
            item_type (CalendarItemType or None): type of scheduled item.
            tree_item (BaseTreeItem or None): tree item representing task,
                if item_type is task.
            event_category (str or None): name to be used for category of item,
                if item_type is event.
            event_name (str or None): name of event, if item_type is event.
            is_background (bool): if True, this is a 'background' item, ie. a
                higher level task or event that subevents or subtasks can be
                overlayed on.
            repeat_pattern (RepeatPattern or None): repeat pattern - unused but
                can be saved in this class so it can be copied over to the new
                one.
        """
        super(CalendarItem, self).__init__(
            calendar,
            start_time=start_time,
            end_time=end_time,
            date=date,
            repeat_pattern=repeat_pattern,
            item_type=item_type,
            tree_item=tree_item,
            event_category=event_category,
            event_name=event_name,
            is_background=is_background
        )

    def datetime_string(self):
        """Get string representing start and end date/time of item.

        Returns:
            (str): string representing date/time of item.
        """
        return "({0} {1} to {2})".format(
            self.date.string(),
            self.start_time.string(),
            self.end_time.string()
        )

    def get_item_container(self, date=None):
        """Get the list that this item should be contained in.

        Args:
            date (Date or None): date to query at. If not given, use the
                item's internal start date time.

        Returns:
            (list): list that calendar item should be contained in.
        """
        if date is None:
            date = self.date
        calendar_day = self._calendar.get_day(date)
        return calendar_day._scheduled_items

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = super(CalendarItem, self).to_dict()
        dict_repr[self.START_DATETIME_KEY] = self.start_datetime.string()
        dict_repr[self.END_DATETIME_KEY] = self.end_datetime.string()
        return dict_repr

    @classmethod
    def from_dict(cls, dict_repr, calendar):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): root calendar object.

        Returns:
            (CalendarItem or None): calendar item, if can be initialised.
        """
        start = dict_repr.get(cls.START_DATETIME_KEY)
        end = dict_repr.get(cls.END_DATETIME_KEY)
        try:
            start_datetime = DateTime.from_string(start)
            end_datetime = DateTime.from_string(end)
        except DateTimeError as e:
            # TODO: either remove this try except, or return None and manage
            # that case in CalendarDay class from_dict method
            raise e
        return super(CalendarItem, cls).from_dict(
            dict_repr,
            calendar,
            start_datetime.time(),
            end_datetime.time(),
            start_datetime.date(),
        )


class RepeatCalendarItem(BaseCalendarItem):
    """Class for repeating calendar items.

    This uses Time values to determine the start and end time of the item
    and a CalendarItemRepeatPattern instance to determine the dates of
    the instances of the item.
    """
    START_TIME_KEY = "start_time"
    END_TIME_KEY = "end_time"
    REPEAT_PATTERN_KEY = "repeat_pattern"
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
            is_background=None):
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
                serialization. Again, these are still keyed by the original
                date they were scheduled for, for easy comparison to the the
                instances dict.
        """
        super(RepeatCalendarItem, self).__init__(
            calendar,
            start_time=start_time,
            end_time=end_time,
            repeat_pattern=repeat_pattern,
            item_type=item_type,
            tree_item=tree_item,
            event_category=event_category,
            event_name=event_name,
            is_background=is_background
        )
        self._instances = OrderedDict()
        self._overridden_instances = {}

    @property
    def start_date(self):
        """Get start date of repeat pattern.

        Returns:
            (Date): date of first instance of repeat calendar item.
        """
        return self.repeat_pattern.start_date

    @property
    def date(self):
        """Override date property to use start date.

        Returns:
            (Date): start date.
        """
        return self.start_date

    def datetime_string(self):
        """Get string representing start and end time of item.

        Returns:
            (str): string representing time of item.
        """
        return "({1} to {2} {0})".format(
            self.start_time.string(),
            self.end_time.string(),
            self.repeat_pattern.summary_string(),
        )

    def get_item_container(self, datetime=None):
        """Get the list that this item should be contained in.

        Args:
            datetime (DateTime or None): datetime to query at. In this class,
                this arg is ignored.

        Returns:
            (list): list that calendar item should be contained in.
        """
        return self._calendar._repeat_items

    def instances_at_date(self, date):
        """Get instances at given date, if some exist.

        Args:
            date (Date): date to check.

        Returns:
            (list(RepeatCalendarItemInstance): list of all repeat calendar item
                instances that exist at the given date. Note that this will
                include any items that are overridden to the current date, and
                will not include items originally scheduled for this date that
                have been moved.
        """
        # first update instances dict to get all of them up to given date
        latest_date = self.start_date
        if self._instances:
            latest_date = list(self._instances.keys())[-1] + TimeDelta(days=1)
        for _date in self.repeat_pattern.dates_between(latest_date, date):
            if _date in self._overridden_instances.keys():
                # if date already accounted for by override, just add it
                self._instances[_date] = self._overridden_instances[_date]
            else:
                # otherwise create new instance
                self._instances[_date] = RepeatCalendarItemInstance(
                    self._calendar,
                    self,
                    _date
                )

        # now find the instances at the current date (scheduled or overridden)
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
        to remove ghost overrides. Overrides should be removed if they meet
        one of the following criteria:
            - their time values no longer override the scheduled time.
            - their initial scheduled date no longer falls in the repeat
                pattern.
        """
        override_tuples = list(self._overridden_instances.items())
        for scheduled_date, instance in override_tuples:
            if (not self._repeat_pattern.check_date(scheduled_date)
                    or not instance.is_override()):
                del self._overridden_instances[scheduled_date]

    def _clear_instances(self):
        """Clear instances list so they can be recalculated.

        This should be called after repeat pattern is changed, to recalculate.
        """
        self._instances = OrderedDict()
        self._clean_overrides()

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = super(RepeatCalendarItem, self).to_dict()
        dict_repr[self.START_TIME_KEY] = self.start_time.string()
        dict_repr[self.END_TIME_KEY] = self.end_time.string()
        dict_repr[self.REPEAT_PATTERN_KEY] = self.repeat_pattern.to_dict()
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
            (RepeatCalendarItem or None): calendar item, if can be initialised.
        """
        try:
            start_time = Time.from_string(dict_repr.get(cls.START_TIME_KEY))
            end_time = Time.from_string(dict_repr.get(cls.END_TIME_KEY))
        except DateTimeError:
            return None
        repeat_pattern = CalendarItemRepeatPattern.from_dict(
            dict_repr.get(cls.REPEAT_PATTERN_KEY)
        )
        repeat_item = super(RepeatCalendarItem, cls).from_dict(
            dict_repr,
            calendar,
            start_time,
            end_time,
            repeat_pattern,
        )
        overrides = dict_repr.get(cls.OVERRIDDEN_INSTANCES_KEY, {})
        for date_str, instance_dict in overrides.items():
            date = Date.from_string(date_str)
            repeat_item._overridden_instances[date] = (
                RepeatCalendarItemInstance.from_dict(
                    instance_dict,
                    repeat_item._calendar,
                    repeat_item,
                    date
                )
            )
        return repeat_item


class RepeatCalendarItemInstance(BaseCalendarItem):
    """Instance of a repeated calendar item.

    This has similar properties to CalendarItem, but inherits all of them from
    the RepeatCalendarItem object it uses as a template.
    """
    OVERRIDE_START_DATETIME_KEY = "start_datetime_override"
    OVERRIDE_END_DATETIME_KEY = "end_datetime_override"

    def __init__(
            self,
            calendar,
            repeat_calendar_item,
            scheduled_date,
            override_start_datetime=None,
            override_end_datetime=None):
        """Initialise class.

        Args:
            calendar (Calendar): the calendar item.
            repeat_calendar_item (RepeatCalendarItem): the repeat calendar item
                that this is an instance of.
            scheduled_date (Date): date this instance is scheduled for.
            override_start_datetime (DateTime or None): start date time to
                override from repeat_item template.
            override_end_datetime (DateTime): start date time to override from
                repeat_item template.
        """
        start_time = None
        end_time = None
        date = None
        if override_start_datetime is not None:
            start_time = override_start_datetime.time()
            date = override_start_datetime.date()
        if override_end_datetime is not None:
            end_time = override_end_datetime.time()

        super(RepeatCalendarItemInstance, self).__init__(
            calendar,
            start_time=start_time,
            end_time=end_time,
            date=date,
            template_item=repeat_calendar_item
        )
        self._scheduled_date = scheduled_date

    @property
    def repeat_calendar_item(self):
        """Get repeat calendar item.

        Returns:
            (RepeatCalendarItem): the repeat calendar item used as a template
                for this item's properties.
        """
        return self._template_item

    @property
    def override_start_time(self):
        """Get start time override.

        Returns:
            (Time or None): start time override.
        """
        return self._start_time.value

    @property
    def override_end_time(self):
        """Get end time override.

        Returns:
            (Time or None): end time override.
        """
        return self._end_time.value

    @property
    def override_date(self):
        """Get date override.

        Returns:
            (Date or None): date override.
        """
        return self._date.value

    @property
    def override_start_datetime(self):
        """Get start datetime override.

        Returns:
            (DateTime or None): start datetime override.
        """
        return DateTime.from_date_and_time(self.date, self.override_start_time)

    @property
    def override_end_datetime(self):
        """Get end datetime override.

        Returns:
            (DateTime or None): end datetime override.
        """
        return DateTime.from_date_and_time(self.date, self.override_end_time)

    @property
    def scheduled_start_time(self):
        """Get scheduled start time.

        Returns:
            (Time): scheduled start time.
        """
        return self.repeat_calendar_item.start_time

    @property
    def scheduled_end_time(self):
        """Get scheduled end time.

        Returns:
            (Time): scheduled end time.
        """
        return self.repeat_calendar_item.end_time

    @property
    def scheduled_date(self):
        """Get date that item is scheduled for (before overrides).

        Returns:
            (Date): scheduled date.
        """
        return self._scheduled_date

    @property
    def scheduled_start_datetime(self):
        """Get scheduled start datetime.

        Returns:
            (DateTime): scheduled start datetime.
        """
        return DateTime.from_date_and_time(
            self.scheduled_date,
            self.scheduled_start_time
        )

    @property
    def scheduled_end_datetime(self):
        """Get scheduled end datetime.

        Returns:
            (DateTime): scheduled end datetime.
        """
        return DateTime.from_date_and_time(
            self.scheduled_date,
            self.scheduled_end_time
        )

    @property
    def date(self):
        """Date instance is at.

        Returns:
            (Date): date of instance.
        """
        if self.override_date:
            return self.override_date
        return self.scheduled_date

    def datetime_string(self):
        """Get string representing start and end date/time of item.

        Returns:
            (str): string representing date/time of item.
        """
        return "({0} {1} to {2})".format(
            self.date.string(),
            self.start_time.string(),
            self.end_time.string()
        )

    def get_item_container(self, datetime=None):
        """Get the list that this item should be contained in.

        Args:
            datetime (DateTime or None): datetime to query at. If not given,
                use the internal date.

        Returns:
            (list): list that calendar item should be contained in.
        """
        raise NotImplementedError(
            "get_item_container is expected to return a list, but repeat "
            "calendar items are stored in dicts. Hence this method is not "
            "implemented for them to avoid confusion, and isn't expected to "
            "be used."
        )

    def is_override(self):
        """Check whether the given instance overrides the repeat template.

        Returns:
            (bool): whether this instance is an override.
        """
        override_start_datetime = self.override_start_datetime
        override_end_datetime = self.override_end_datetime
        if override_start_datetime is not None:
            if override_start_datetime != self.scheduled_start_datetime:
                return True
        if override_end_datetime is not None:
            if override_end_datetime != self.scheduled_end_datetime:
                return True
        return False

    def _compute_override(self):
        """Check if this is override and add/remove it from overrides list."""
        overrides = self.repeat_calendar_item._overridden_instances
        if self.is_override():
            overrides[self.scheduled_date] = self
        else:
            if self.scheduled_date in overrides:
                del overrides[self.scheduled_date]

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = {}
        if self.override_start_datetime:
            dict_repr[self.OVERRIDE_START_DATETIME_KEY] = (
                self.override_start_datetime.string()
            )
        if self.override_end_datetime:
            dict_repr[self.OVERRIDE_END_DATETIME_KEY] = (
                self.override_end_datetime.string()
            )
        return dict_repr

    @classmethod
    def from_dict(
            cls,
            dict_repr,
            calendar,
            repeat_calendar_item,
            scheduled_date):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            repeat_calendar_item (RepeatCalendarItem): the repeat calendar item
                that this is an instance of.
            scheduled_date (Date): original scheduled date of item.

        Returns:
            (BaseCalendarItem or None): calendar item, if can be initialised.
        """
        override_start_datetime = None
        override_end_datetime = None
        start_string = dict_repr.get(cls.OVERRIDE_START_DATETIME_KEY)
        end_string = dict_repr.get(cls.OVERRIDE_END_DATETIME_KEY)
        try:
            if start_string:
                override_start_datetime = DateTime.from_string(start_string)
            if end_string:
                override_end_datetime = DateTime.from_string(end_string)
        # TODO: these from_dict excepts need loggers to explain what's happened
        except DateTimeError:
            return None
        return cls(
            calendar,
            repeat_calendar_item,
            scheduled_date,
            override_start_datetime,
            override_end_datetime
        )
