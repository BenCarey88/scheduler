"""Scheduled item class."""

from collections import OrderedDict
from functools import partial

from scheduler.api.common.date_time import (
    Date,
    DateTime,
    DateTimeError,
    Time,
    TimeDelta,
)
from scheduler.api.common.object_wrappers import (
    Hosted,
    HostedDataDict,
    HostedDataList,
    MutableAttribute,
    MutableHostedAttribute,
)
from scheduler.api.common.timeline import TimelineDict
from scheduler.api.serialization import item_registry
from scheduler.api.serialization.serializable import (
    NestedSerializable,
    SaveType,
)
from scheduler.api.tree.task import Task
from scheduler.api.tree.task_category import TaskCategory
from scheduler.api import constants
from scheduler.api.enums import OrderedStringEnum, ItemStatus, ItemUpdatePolicy
from scheduler.api.utils import fallback_value
from .repeat_pattern import RepeatPattern
from ._base_calendar_item import BaseCalendarItem


#TODO standardize exceptions
class ScheduledItemError(Exception):
    """Generic exception for scheduled item errors."""


class ScheduledItemType(OrderedStringEnum):
    """Struct defining types of scheduled items."""
    TASK = "task"
    EVENT = "event"


class BaseScheduledItem(BaseCalendarItem):
    """Base scheduled item class representing a scheduled task or event.

    This class doesn't include any datetime information as the way this data
    is used and serialized varies depending on whether the item repeats or not,
    so this is implemented in the subclasses.
    """
    TYPE_KEY = "type"
    TREE_ITEM_KEY = "tree_item"
    NAME_KEY = "name"
    CATEGORY_KEY = "category"
    BACKGROUND_KEY = "background"

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
            task_update_policy=None,
            is_background=None,
            template_item=None,
            status=None):
        """Initialise item.

        Args:
            calendar (Calendar): calendar class instance.
            start_time (Time or None): time item starts at.
            end_time (Time or None): time item ends at.
            date (Date or None): date item starts at.
            repeat_pattern (RepeatPattern or None): repeat pattern of item.
                This is only used for repeat scheduled items, but can be stored
                in standard scheduled items so it's saved when converting to a
                repeat one.
            item_type (ScheduledItemType or None): type of scheduled item.
            tree_item (BaseTaskItem or None): tree item representing task,
                if item_type is task.
            event_category (str or None): name to be used for category of item,
                if item_type is event.
            event_name (str or None): name of event, if item_type is event.
            task_update_policy (ItemUpdatePolicy or None): update policy for
                linked task.
            is_background (bool): if True, this is a 'background' item, ie. a
                higher level task or event that subevents or subtasks can be
                overlayed on.
            template_item (BaseScheduledItem or None): template item to inherit
                properties from, if they're not overridden. This is used by
                RepeatScheduledItemInstances.
            status (ItemStatus or None): status of item.
        """
        super(BaseScheduledItem, self).__init__(
            calendar,
            tree_item,
            status,
            task_update_policy=task_update_policy,
        )
        self._is_scheduled_item = True
        self._task_root = calendar.task_root
        self._template_item = template_item
        if template_item is None:
            # if we can't inherit from a template item, set default values
            item_type = item_type or ScheduledItemType.TASK
            event_category = event_category or ""
            event_name = event_name or ""
            is_background = is_background or False

        self._start_time = MutableAttribute(start_time, "start_time")
        self._end_time = MutableAttribute(end_time, "end_time")
        self._date = MutableAttribute(date, "date")
        self._repeat_pattern = MutableAttribute(
            repeat_pattern,
            "repeat_pattern",
        )
        self._type = MutableAttribute(item_type, "type")
        self._event_category = MutableAttribute(
            event_category,
            "event_category",
        )
        self._event_name = MutableAttribute(event_name, "event_name")
        self._is_background = MutableAttribute(is_background, "is_background")

    class _Decorators(object):
        """Internal decorators class."""
        # TODO: make this a method that returns a decorator instead,
        # with an arg allowing you to specify the default return value
        # - currently it only searches the template item if the value
        # comes out as None, but in some cases False or "" may be the
        # default
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
                    definitions in the RepeatScheduledItemInstance class. It
                    means that RepeatScheduledItemInstances can rely on their
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
            return DateTime.from_date_and_time(self.date, self.end_time)
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
        """Get type of scheduled item.

        Returns:
            (ScheduledItemType): item type.
        """
        return self._type.value

    @property
    @_template_item_decorator
    def tree_item(self):
        """Get tree item representing task.

        This is reimplimented from base class to add the template decorator.

        Returns:
            (BaseTaskItem or None): task or task category tree item, if one
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
        if self.type == ScheduledItemType.TASK:
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
        if self.type == ScheduledItemType.TASK:
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

    @property
    @_template_item_decorator
    def status(self):
        """Get check status of item.

        This is reimplimented from base class to add the template decorator.

        Returns:
            (ItemStatus): status of item.
        """
        return max(self._status.value, self._status_from_children.value)

    @property
    def defunct(self):
        """Override defunct property.

        Returns:
            (bool): whether or not item should be considered deleted.
        """
        return super(BaseScheduledItem, self).defunct or (
            self.type == ScheduledItemType.TASK
            and self.tree_item is None
        )

    @property
    def planned_items(self):
        """Get planned item parents associated to this one.

        Usually there would just be the one, but we want to allow multiple,
        eg. you plan /writing/planning and /writing/first_draft and then
        schedule them both with a single writing scheduled item.

        Returns:
            (list(PlannedItem)): list of planned items.
        """
        return self._parents

    def is_task(self):
        """Check if this item has task type.

        Returns:
            (bool): whether or not item has task type.
        """
        return (self.type == ScheduledItemType.TASK)

    def is_repeat(self):
        """Check if this item is repeating.

        Returns:
            (bool): whether or not this is a repeat item.
        """
        return False

    def is_repeat_instance(self):
        """Check if this item is a repeat instance.

        Returns:
            (bool): whether or not this is a repeat item instance.
        """
        return False

    def datetime_string(self):
        """Get string representing start and end date/time of item.

        Returns:
            (str): string representing date/time of item.
        """
        raise NotImplementedError(
            "datetime_string is implemented in scheduled item subclasses."
        )

    def get_item_container(self, date=None):
        """Get the list that this item should be contained in.

        Args:
            date (Date or None): date to query at. If not given, use the
                item's internal start date time.

        Returns:
            (list): list that scheduled item should be contained in.
        """
        raise NotImplementedError(
            "get_item_container is implemented in scheduled item subclasses."
        )

    def _get_task_to_update(
            self,
            new_type=None,
            new_tree_item=None,
            new_template_type=None,
            new_template_tree_item=None):
        """Utility method to return the linked task item if it needs updating.

        This is used only by edit classes that update the task history based
        on updates to this scheduled item.

        Args:
            new_type (TaskType or None): new type that the scheduled item will
                have, if needed.
            tree_item (BaseTaskItem or None): new linked tree item the
                scheduled item will have, if needed.
            new_template_type (TaskType or None): new type that the scheduled
                item's template item will have, if needed.
            new_template_tree_item (BaseTaskItem or None): new linked tree item
                that the scheduled item's template item will have, if needed.

        Returns:
            (Task or None): linked tree item, if it's a task, and the scheduled
                item is a task.
        """
        type_fallbacks = [new_type, self.type]
        task_fallbacks = [new_tree_item, self.tree_item]
        if self._template_item is not None:
            type_fallbacks[1:1] = [self._type.value, new_template_type]
            task_fallbacks[1:1] = [
                self._tree_item.value, new_template_tree_item
            ]
        type_ = fallback_value(*type_fallbacks)
        task_item = fallback_value(*task_fallbacks)
        if type_ != ScheduledItemType.TASK:
            return None
        if not isinstance(task_item, Task):
            return None
        return task_item

    def _iter_influences(self):
        """Get tasks influenced at datetimes by this item or its instances.

        - for a normal scheduled item, or a scheduled item instance, this should
            return max one task at one time.
        - for a repeat scheduled item, this should return all tasks influenced
            by any instance of the repeat item (and hence we need to
            reimplement this method in that class)

        Yields:
            (BaseScheduledItem): the scheduled item (or repeat item instance)
                that's doing the influencing - will be this item or an instance
                of it.
            (Task): the influenced task.
            (Date or DateTime): the date or datetime it influences at.
        """
        task = self._get_task_to_update()
        if task is not None:
            # TODO: if/when we implement scheduled items over whole dates
            # include the logic here to allow date influencers
            date_time = self.end_datetime
            influencer_dict = task.history.get_influencer_dict(
                date_time,
                self,
            )
            if influencer_dict:
                yield (self, task, date_time)

    def _get_id(self):
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
        dict_repr = super(BaseScheduledItem, self).to_dict()
        if not self.is_repeat_instance():
            # don't need to save this stuff for repeat instances
            if self._type:
                dict_repr[self.TYPE_KEY] = self._type.value
            if self.type == ScheduledItemType.EVENT:
                if self._event_category:
                    dict_repr[self.CATEGORY_KEY] = self._event_category.value
                if self._event_name:
                    dict_repr[self.NAME_KEY] = self._event_name.value
            if self._is_background:
                dict_repr[self.BACKGROUND_KEY] = self._is_background.value
        return dict_repr

    @classmethod
    def from_dict(
            cls,
            dict_repr,
            calendar,
            *init_args,
            is_instance=False,
            **init_kwargs):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            calendar (Calendar): root calendar object.
            date_args (list): additional args to pass to __init__. These will
                all be passed to the start of the init __function__.
            is_instance (bool): if True, this is a repeat instance and so
                we can skip a large proportion of the init args, since these
                don't get saved and are just inherited from the template item.

        Returns:
            (BaseScheduledItem or None): scheduled item, if can be initialised.
        """
        if is_instance:
            scheduled_item = super(BaseScheduledItem, cls).from_dict(
                dict_repr,
                calendar,
                *init_args,
                **init_kwargs,
            )
        else:
            item_type = dict_repr.get(cls.TYPE_KEY)
            category = dict_repr.get(cls.CATEGORY_KEY)
            name = dict_repr.get(cls.NAME_KEY)
            is_background = dict_repr.get(cls.BACKGROUND_KEY, False)
            scheduled_item = super(BaseScheduledItem, cls).from_dict(
                dict_repr,
                calendar,
                *init_args,
                item_type=item_type,
                event_category=category,
                event_name=name,
                is_background=is_background,
                **init_kwargs,
            )
        return scheduled_item


class ScheduledItem(BaseScheduledItem):
    """Scheduled item class representing a scheduled task or event.

    This uses DateTime values to define the start and end date and time of
    the item.
    """
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
            task_update_policy=None,
            is_background=None,
            status=None,
            repeat_pattern=None):
        """Initialise item.

        Args:
            calendar (Calendar): calendar class instance.
            start_datetime (Time): start time.
            end_datetime (Time): end time.
            date (Date): date of item.
            item_type (ScheduledItemType or None): type of scheduled item.
            tree_item (BaseTaskItem or None): tree item representing task,
                if item_type is task.
            event_category (str or None): name to be used for category of item,
                if item_type is event.
            event_name (str or None): name of event, if item_type is event.
            task_update_policy (ItemUpdatePolicy or None): update policy for
                linked task.
            is_background (bool): if True, this is a 'background' item, ie. a
                higher level task or event that subevents or subtasks can be
                overlayed on.
            status (ItemStatus or None): status of item.
            repeat_pattern (RepeatPattern or None): repeat pattern - unused but
                can be saved in this class so it can be copied over to the new
                one.
        """
        super(ScheduledItem, self).__init__(
            calendar,
            start_time=start_time,
            end_time=end_time,
            date=date,
            repeat_pattern=repeat_pattern,
            item_type=item_type,
            tree_item=tree_item,
            event_category=event_category,
            event_name=event_name,
            task_update_policy=task_update_policy,
            is_background=is_background,
            status=status,
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
                item's internal start date.

        Returns:
            (list): list that scheduled item should be contained in.
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
        dict_repr = super(ScheduledItem, self).to_dict()
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
            (ScheduledItem or None): scheduled item, if can be initialised.
        """
        start = dict_repr.get(cls.START_DATETIME_KEY)
        end = dict_repr.get(cls.END_DATETIME_KEY)
        start_datetime = DateTime.from_string(start)
        end_datetime = DateTime.from_string(end)
        scheduled_item = super(ScheduledItem, cls).from_dict(
            dict_repr,
            calendar,
            start_datetime.time(),
            end_datetime.time(),
            start_datetime.date(),
        )
        # scheduled_item._activate()
        return scheduled_item


# TODO: allow overriding to delete instances too
class RepeatScheduledItem(BaseScheduledItem):
    """Class for repeating scheduled items.

    This uses Time values to determine the start and end time of the item
    and a RepeatPattern instance to determine the dates of the instances
    of the item.
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
            task_update_policy=None,
            is_background=None,
            status=None):
        """Initialise item.

        Args:
            calendar (Calendar): calendar class instance.
            start_time (Time): start time.
            end_time (Time): end time.
            repeat_pattern (RepeatPattern): repeat pattern object, describing
                what days this item repeats on.
            item_type (ScheduledItemType or None): type of scheduled item.
            tree_item (BaseTaskItem or None): tree item representing task,
                if item_type is task.
            event_category (str or None): name to be used for category of item,
                if item_type is event.
            event_name (str or None): name of event, if item_type is event.
            task_update_policy (ItemUpdatePolicy or None): update policy for
                linked task.
            is_background (bool): if True, this is a 'background' item, ie. a
                higher level task or event that subevents or subtasks can be
                overlayed on.
            status (ItemStatus or None): status of item.

        Attributes:
            _instances (dict(Date, RepeatScheduledItemInstance)): dictionary of
                instances of this repeat item, keyed by the date they're
                scheduled for originally. If the item has it's date overridden,
                the date key remains unchanged.
            _overridden_instances (dict(Date, RepeatScheduledItemInstance)):
                dictionary of all instances that have overrides on their time/
                date/status etc. These are the only ones that need to be saved
                during serialization. Again, these are still keyed by the
                original date they were scheduled for, for easy comparison to
                the instances dict.
            _task_influences (dict(DateTime, RepeatScheduledItemInstance)):
                dict of datetimes that instances of this item influence tasks
                at.
        """
        super(RepeatScheduledItem, self).__init__(
            calendar,
            start_time=start_time,
            end_time=end_time,
            repeat_pattern=repeat_pattern,
            item_type=item_type,
            tree_item=tree_item,
            event_category=event_category,
            event_name=event_name,
            task_update_policy=task_update_policy,
            is_background=is_background,
            status=status,
        )
        self._instances = OrderedDict()
        self._overridden_instances = {}
        # TODO: will the below be needed? might be required to make sure that
        # we don't delete instances that are currently influencing a task? Or
        # at least to flag up to the user that the edit they're about to do
        # will cause the deletion of an influence
        self._task_influences = OrderedDict()

    @property
    def start_date(self):
        """Get start date of repeat pattern.

        Returns:
            (Date): date of first instance of repeat scheduled item.
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
        return "({0} to {1} {2})".format(
            self.start_time.string(),
            self.end_time.string(),
            self.repeat_pattern.summary_string(),
        )

    def is_repeat(self):
        """Check if this item is repeating.

        Returns:
            (bool): whether or not this is a repeat item.
        """
        return True

    def get_item_container(self, date=None):
        """Get the list that this item should be contained in.

        Args:
            date (Date or None): date to query at. If not given, use the
                item's internal start date time.

        Returns:
            (list): list that scheduled item should be contained in.
        """
        return self._calendar._repeat_items

    def instances_at_date(self, date):
        """Get instances at given date, if some exist.

        Args:
            date (Date): date to check.

        Returns:
            (list(RepeatScheduledItemInstance): list of all repeat scheduled item
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
                self._instances[_date] = (
                    RepeatScheduledItemInstance.create_and_activate(
                        self._calendar,
                        self,
                        _date,
                    )
                )
                # ^since repeat instances aren't added directly as edits, we
                # need to activate them to make the hosted data stuff work
                # TODO: look over this, it's a bit unnerving and messy

        # now find the instances at the current date (scheduled or overridden)
        instances_at_date = []
        scheduled_instance = self._instances.get(date, None)
        if scheduled_instance and scheduled_instance.date == date:
            instances_at_date.append(self._instances[date])
        for instance in self._overridden_instances.values():
            if instance.date == date and instance != scheduled_instance:
                instances_at_date.append(instance)
        return instances_at_date

    #TODO delete, I've just switched this out in the edit method for a
    # DictEdit, remove this function assuming we don't get bugs with the new
    # edit setup
    # def _clean_overrides(self):
    #     """Remove overrides that no longer apply.

    #     This should be called after the repeat pattern or times are changed,
    #     to remove ghost overrides. Overrides should be removed if they meet
    #     one of the following criteria:
    #         - their initial scheduled date no longer falls in the repeat
    #             pattern (in this case, they're not only no longer overrides
    #             but in fact no longer instances and so should be deactivated).
    #         - their attributes no longer override the templated attributes.
    #     """
    #     override_tuples = list(self._overridden_instances.items())
    #     for scheduled_date, instance in override_tuples:
    #         if not self.repeat_pattern.check_date(scheduled_date):
    #             # TODO: look over this, it's a bit unnerving and messy
    #             # to be manually deactivating so often
    #             self._overridden_instances[scheduled_date]._deactivate()
    #             del self._overridden_instances[scheduled_date]
    #         elif not instance.is_override():
    #             del self._overridden_instances[scheduled_date]

    def _clear_instances(self):
        """Clear instances list so they can be recalculated.

        This should be called after repeat pattern is changed, to recalculate.
        """
        # since repeat instances aren't removed directly as edits, we
        # need to deactivate them to make the hosted data stuff work
        # TODO: look over this, it's a bit unnerving and messy
        # for key, instance in self._instances.items():
        #     if key not in self._overridden_instances:
        #         instance._deactivate()
        # TODO ^delete above comments assuming the new edit setup is all fine
        self._instances = OrderedDict()
        # self._clean_overrides()

    def _iter_overrides(self):
        """Iterate through overridden instances.

        Yields:
            (RepeatScheduledItemInstance): the next instance.
        """
        for instance in self._overridden_instances.values():
            yield instance

    def _iter_influences(self):
        """Get tasks influenced at datetimes by this item or its instances.

        This is reimplemented from the base definition to return all tasks
        influenced by any instance of this item.

        Yields:
            (BaseScheduledItem): the repeat item instance that's doing the
                influencing.
            (Task): the influenced task.
            (Date or DateTime): the date or datetime it influences at.
        """
        # NOTE this assumes that only overrides can be influencers. IF
        # we allow the OVERRIDE update policy then this may not be the case
        # as an instance with UNSTARTED status (which will therefore not
        # override the status of its template and not be counted as an
        # override) would still influence its linked task
        for item_instance in self._iter_overrides():
            for return_tuple in item_instance._iter_influences():
                yield return_tuple

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = super(RepeatScheduledItem, self).to_dict()
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
            (RepeatScheduledItem or None): scheduled item, if can be initialised.
        """
        try:
            start_time = Time.from_string(dict_repr.get(cls.START_TIME_KEY))
            end_time = Time.from_string(dict_repr.get(cls.END_TIME_KEY))
        except DateTimeError:
            return None
        repeat_pattern = RepeatPattern.from_dict(
            dict_repr.get(cls.REPEAT_PATTERN_KEY)
        )
        repeat_item = super(RepeatScheduledItem, cls).from_dict(
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
                RepeatScheduledItemInstance.from_dict(
                    instance_dict,
                    repeat_item._calendar,
                    repeat_item,
                    date,
                )
            )
        # repeat_item._activate()
        return repeat_item


class RepeatScheduledItemInstance(BaseScheduledItem):
    """Instance of a repeated scheduled item.

    This has similar properties to ScheduledItem, but inherits all of them from
    the RepeatScheduledItem object it uses as a template.
    """
    OVERRIDE_START_DATETIME_KEY = "start_datetime_override"
    OVERRIDE_END_DATETIME_KEY = "end_datetime_override"

    _SERIALIZE_TREE_ITEM = False

    def __init__(
            self,
            calendar,
            repeat_scheduled_item,
            scheduled_date,
            override_start_datetime=None,
            override_end_datetime=None,
            task_update_policy=None,
            tree_item=None,
            status=None):
        """Initialise class.

        Args:
            calendar (Calendar): the scheduled item.
            repeat_scheduled_item (RepeatScheduledItem): the repeat scheduled
                item that this is an instance of.
            scheduled_date (Date): date this instance is scheduled for.
            override_start_datetime (DateTime or None): start date time to
                override from repeat_item template.
            override_end_datetime (DateTime): start date time to override from
                repeat_item template.
            task_update_policy (ItemUpdatePolicy or None): update policy for
                linked task. Ignored in this case because its inherited from
                the template item but needs to be passed because of super class
                from_dict methods.
            tree_item (BaseTaskItem or None): tree item to associate. Ignored
                in this case because its inherited from the template item but
                needs to be passed because of super class from_dict methods.
            status (ItemStatus or None): status of item.
        """
        start_time = None
        end_time = None
        date = None
        if override_start_datetime is not None:
            start_time = override_start_datetime.time()
            date = override_start_datetime.date()
        if override_end_datetime is not None:
            end_time = override_end_datetime.time()

        super(RepeatScheduledItemInstance, self).__init__(
            calendar,
            start_time=start_time,
            end_time=end_time,
            date=date,
            template_item=repeat_scheduled_item,
            status=status,
        )
        self._scheduled_date = scheduled_date

    @property
    def repeat_scheduled_item(self):
        """Get repeat scheduled item.

        Returns:
            (RepeatScheduledItem): the repeat scheduled item used as a template
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
        if self.override_start_time is None:
            return None
        return DateTime.from_date_and_time(self.date, self.override_start_time)

    @property
    def override_end_datetime(self):
        """Get end datetime override.

        Returns:
            (DateTime or None): end datetime override.
        """
        if self.override_end_time is None:
            return None
        return DateTime.from_date_and_time(self.date, self.override_end_time)

    @property
    def scheduled_start_time(self):
        """Get scheduled start time.

        Returns:
            (Time): scheduled start time.
        """
        return self.repeat_scheduled_item.start_time

    @property
    def scheduled_end_time(self):
        """Get scheduled end time.

        Returns:
            (Time): scheduled end time.
        """
        return self.repeat_scheduled_item.end_time

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

    @property
    def task_update_policy(self):
        """Get update policy for linked tasks.

        This is inherited from the template item. We can use the template item
        decorator however because the value of this property is never None (it
        defaults to ItemUpdatePolicy.UNSTARTED)

        Returns:
            (ItemUpdatePolicy): update policy for linked tasks.
        """
        return self._template_item.task_update_policy

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

    def _get_tree_item_pairing_id(self):
        """Override pairing id to opt out of pairing framework.

        Returns:
            (None): None - this means that there is no pairing, so the
                tree item doesn't keep a list of all scheduled instances
                associated to it. Instead it just keeps a list of all
                repeat items associated to it.
        """
        return None

    def get_item_container(self, date=None):
        """Get the list that this item should be contained in.

        Args:
            date (Date or None): date to query at. If not given, use the
                item's internal start date time.

        Returns:
            (list): list that scheduled item should be contained in.
        """
        raise NotImplementedError(
            "get_item_container is expected to return a list, but repeat "
            "scheduled items are stored in dicts. Hence this method is not "
            "implemented for them to avoid confusion, and isn't expected to "
            "be used."
        )

    def is_repeat_instance(self):
        """Check if this item is a repeat instance.

        Returns:
            (bool): whether or not this is a repeat item instance.
        """
        return True

    def is_override(
            self,
            template_start_time=None,
            template_end_time=None,
            template_status=None,
            instance_date=None,
            instance_start_time=None,
            instance_end_time=None,
            instance_status=None):
        """Check whether the given instance overrides the repeat template.

        An item is an override if one of the following is true:
            - its start or end datetime is overridden from the template
            - its status is overridden from the template

        The optional args are added to allow edit classes to check whether
        this item will be an override after various changes are made to
        this instance or its template item.

        Args:
            template_start_time (Time or None): new template start time.
            template_status (ItemStatus or None): new template status.
            instance_date (Date or None): new instance date.
            instance_start_time (Time or None): new instance start time.
            instance_end_time (Time or None): new instance start time.
            instance_status (ItemStatus or None): new instance status.

        Returns:
            (bool): whether this instance is an override.
        """
        # NOTE: any update to this function needs to also be reflected in
        # conditions for triggering the _clean_overrides subedit in the
        # ModifyRepeatScheduledItemEdit, and the _compute_override subedit
        # in the ModifyRepeatScheduledItemInstanceEdit.

        # date
        instance_date = fallback_value(instance_date, self.date)
        if instance_date != self.scheduled_date:
            return True

        # start time
        instance_start_time = fallback_value(
            instance_start_time,
            self.start_time,
        )
        template_start_time = fallback_value(
            template_start_time,
            self.repeat_scheduled_item.start_time,
        )
        if instance_start_time != template_start_time:
            return True

        # end time
        instance_end_time = fallback_value(
            instance_end_time,
            self.end_time,
        )
        template_end_time = fallback_value(
            template_end_time,
            self.repeat_scheduled_item.end_time,
        )
        if instance_end_time != template_end_time:
            return True

        # status
        instance_status = fallback_value(instance_status, self.status)
        template_status = fallback_value(
            template_status,
            self.repeat_scheduled_item.status,
        )
        if instance_status != template_status:
            return True

        return False

    #TODO delete, I've just switched this out in the edit method for a
    # DictEdit, remove this function assuming we don't get bugs with the new
    # edit setup
    # def _compute_override(self):
    #     """Check if this is override and add/remove it from overrides list."""
    #     overrides = self.repeat_scheduled_item._overridden_instances
    #     if self.is_override():
    #         overrides[self.scheduled_date] = self
    #     else:
    #         if self.scheduled_date in overrides:
    #             del overrides[self.scheduled_date]

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        dict_repr = super(RepeatScheduledItemInstance, self).to_dict()
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
            repeat_scheduled_item,
            scheduled_date):
        """Initialise class from dict.

        Args:
            dict_repr (dict): dictionary representing class.
            repeat_scheduled_item (RepeatScheduledItem): the repeat scheduled
                item that this is an instance of.
            scheduled_date (Date): original scheduled date of item.

        Returns:
            (BaseScheduledItem or None): scheduled item, if can be initialised.
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
        repeat_scheduled_item_instance = super(
            RepeatScheduledItemInstance, cls
        ).from_dict(
            dict_repr,
            calendar,
            repeat_scheduled_item,
            scheduled_date,
            override_start_datetime,
            override_end_datetime,
            is_instance=True,
        )
        return repeat_scheduled_item_instance
