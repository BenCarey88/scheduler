"""Tracker file reader."""

from scheduler.api.enums import (
    CompositionOperator,
    OrderedStringEnum,
    TrackedValueType,
)
from scheduler.api.common.object_wrappers import (
    MutableAttribute,
    HostedDataList,
    Hosted,
)
from scheduler.api.serialization.serializable import BaseSerializable


class TrackerError(Exception):
    """General exception for tracker errors."""


# TODO update this class to allow tracking of non-task items, AND tracking of
# task items with a different value type from the one set in the task?
#
# need to include a history dict for non-task items (can still use
# TaskHistory class, although maybe that could do with renaming?)
class TrackedItem(Hosted, BaseSerializable):
    """Tracked item class for tracked tasks or other trackables."""
    TASK_ITEM_KEY = "task_item"
    NAME_KEY = "name"
    VALUE_TYPE_KEY = "value_type"

    def __init__(self, task_item=None, name=None, value_type=None):
        """Initialize class.

        Args:
            task_item (BaseTaskItem or None): task item to track, if used.
            name (str or None): name to use for tracked item.
            value_type (TrackedItemValueType or None): value type of item.
        """
        super(TrackedItem, self).__init__()
        if task_item is None and (name is None or value_type is None):
            raise ValueError(
                "TrackedItem class must accept a task item or name and "
                "value_type args."
            )
        self._task_item = task_item
        self._name = MutableAttribute(name, "name")
        self._value_type = MutableAttribute(value_type, "value_type")

    @property
    def task_item(self):
        """Get task item that this item tracks, if exists.

        Returns:
            (BaseTaskItem or None): tracked task, if this item is a task.
        """
        return self._task_item

    @property
    def name(self):
        """Get name of this item.

        Returns:
            (str): name of trakced item.
        """
        if self._name.value is not None:
            return self._name.value
        if self.task_item is not None:
            return self.task_item.name
        return ""
    
    @property
    def value_type(self):
        """Get value type of this item.

        Returns:
            (TrackedValueType): type of value this item tracks.
        """
        if self._value_type.value is not None:
            return self._value_type.value
        if self.task_item is not None:
            return self.task_item.value_type
        return TrackedValueType.NONE

    def to_dict(self):
        """Get json compatible dictionary representation of class.

        Returns:
            (OrderedDict): dictionary representation.
        """
        json_dict = {}
        if self.task_item is not None:
            json_dict[self.TASK_ITEM_KEY] = self.task_item.path
        if self._name.value is not None:
            json_dict[self.NAME_KEY] = self._name.value
        if self._value_type.value is not None:
            json_dict[self.VALUE_TYPE_KEY] = self._value_type.value
        return json_dict

    @classmethod
    def from_dict(cls, json_dict, task_root):
        """Initialise class from dictionary representation.

        The json_dict is expected to be structured as described in the to_dict
        docstring.

        Args:
            json_dict (OrderedDict): dictionary representation.
            task_root (TaskRoot): task root item, used to get linked task.

        Returns:
            (TrackedItem): tracked item for given dict.
        """
        task = json_dict.get(cls.TASK_ITEM_KEY)
        if task is not None:
            task = task_root.get_item_at_path(task, search_archive=True)
        name = json_dict.get(cls.NAME_KEY)
        value_type = TrackedValueType.from_string(
            json_dict.get(cls.VALUE_TYPE_KEY)
        )
        return cls(task_item=task, name=name, value_type=value_type)


class TargetOperator(OrderedStringEnum):
    """Operators for setting tracked item targets."""
    LESS_THAN_EQ = "at most"
    GREATER_THAN_EQ = "at least"

    @classmethod
    def get_custom_name(cls, target_operator, value_type):
        """Get custom name of operator for given value type.

        Args:
            target_operator (TargetOperator): the target operator to get a
                custom name for.
            value_type (TrackedValueType): the tracked value type.

        Returns:
            (str): name for target operator that corresponds to the given
                value type.
        """
        operator_dict = {
            cls.LESS_THAN_EQ: {
                TrackedValueType.TIME: "by",
            },
            cls.GREATER_THAN_EQ: {
                TrackedValueType.TIME: "from",
            },
        }.get(target_operator, {})
        return operator_dict.get(value_type, target_operator.value)


# TODO: break this whole page out into a separate top-level tracking module?
class BaseTrackerTarget(object):
    """Base class for tracked item targets."""
    def __init__(self):
        """Initialize class."""
        pass

    def __or__(self, target):
        """Combine this with given target to make a less restrictive target.

        Args:
            target (BaseTrackerTarget): target to combine with.

        Returns:
            (BaseTrackerTarget): target that is met if either the original
                target (self) is met or this new target is met.
        """
        if not isinstance(target, BaseTrackerTarget):
            raise TrackerError(
                "Cannot combine target with non-target class {0}".format(
                    target.__class__.__name__
                )
            )
        # create composite target from the two targets
        subtargets_list = []
        for t in (self, target):
            if (isinstance(t, CompositeTrackerTarget)
                    and t._compositon_operator == CompositionOperator.OR):
                subtargets_list.extend(t._subtargets_list)
            else:
                subtargets_list.append(t)
        return CompositeTrackerTarget(
            subtargets_list,
            CompositionOperator.OR,
        )

    def __and__(self, target):
        """Combine this with given target to make a more restrictive target.

        Args:
            target (BaseTrackerTarget): target to combine with.

        Returns:
            (BaseTrackerTarget): target that is met if both the original
                target (self) is met and this new target is met.
        """
        if not isinstance(target, BaseTrackerTarget):
            raise TrackerError(
                "Cannot combine target with non-target class {0}".format(
                    target.__class__.__name__
                )
            )
        # create composite target from the two targets
        subtargets_list = []
        for t in (self, target):
            if (isinstance(t, CompositeTrackerTarget)
                    and t._compositon_operator == CompositionOperator.AND):
                subtargets_list.extend(t._subtargets_list)
            else:
                subtargets_list.append(t)
        return CompositeTrackerTarget(
            subtargets_list,
            CompositionOperator.AND,
        )

    def is_met_by(self, value):
        """Check if the given tracked value means this target has been met.

        Args:
            value (variant): a value for the tracked task that this target
                has been set for.

        Returns:
            (bool): whether or not the given value meets the target.
        """
        raise NotImplementedError(
            "is_met_by method must be implemented in BaseTrackerTaarget "
            "subclasses"
        )
    
    @classmethod
    def from_dict(cls, dictionary):
        """Initialise class from dictionary.

        Args:
            dictionary (dict): the dictionary we're deserializing from.
        """
        raise NotImplementedError(
            "from_dict method must be implemented in BaseTrackerTaarget "
            "subclasses"
        )

    def to_dict(self):
        """Serialize class as dictionary.

        Returns:
            (dict): the serialized dictionary.
        """
        raise NotImplementedError(
            "to_dict method must be implemented in BaseTrackerTaarget "
            "subclasses"
        )


class TrackerTarget(BaseTrackerTarget):
    """Class defining a target for a tracked item."""
    def __init__(self, time_period, operator, target_value):
        """Initialize target.

        Args:
            time_period (TimePeriod or TimeDelta): time period that target
                is set over (eg. every day, every week, every three days etc.)
            operator (): eg. less than or greater than.
            target_value (variant): value to use with operator (eg. if target
                is before 5:30, use operator 'less than' and value 5:30)
        """
        # TODO: should this even be part of class?
        self._time_period = time_period
        self._operator = operator
        self._target_value = target_value
        super(BaseTrackerTarget, self).__init__()

    # TODO: normalise this, ie. make it always a timedelta?
    @property
    def time_period(self):
        """Get time period that target is set over.

        Returns:
            (TimePeriod or TimeDelta): time period that target is set over.
        """
        return self._time_period

    def is_met_by(self, value):
        """Check if the given tracked value means this target has been met.

        Args:
            value (variant): a value for the tracked task that this target
                has been set for.

        Returns:
            (bool): whether or not the given value meets the target.
        """
        if self._operator == TargetOperator.LESS_THAN_EQ:
            return (value <= self._target_value)
        if self._operator == TargetOperator.GREATER_THAN_EQ:
            return (value >= self._target_value)
        raise TrackerError(
            "Target operation not yet defined for operator {0}".format(
                self._operator
            )
        )


# TODO: this should be over a time_period as well
# TODO: need to_dict and from_dict methods for this and above class
class CompositeTrackerTarget(BaseTrackerTarget):
    """Class for combining tracked item targets."""
    def __init__(self, subtargets_list, composition_operator=None):
        """Initialize target.

        Args:
            subtargets_list (list(TrackedItemTarget)): list of targets.
            composition_operator (CompositionOperator or None): target
                composition operator (must be AND or OR). Defaults to AND.
        """
        super(CompositeTrackerTarget, self).__init__()
        self._subtargets_list = subtargets_list or []
        self._compositon_operator = (
            composition_operator or CompositionOperator.AND
        )

    def is_met_by(self, value):
        """Check if the given tracked value means this target has been met.

        Args:
            value (variant): a value for the tracked task that this target
                has been set for.

        Returns:
            (bool): whether or not the given value meets the target.
        """
        boolean_op = {
            CompositionOperator.OR: any,
            CompositionOperator.AND: all,
        }.get(self._compositon_operator)
        if boolean_op is None:
            raise TrackerError(
                "Unsupported target compositon operator {0}".format(
                    self._compositon_operator
                )
            )

        return boolean_op(
            (target.is_met_by(value) for target in self._subtargets_list)
        )


class Tracker(BaseSerializable):
    """Tracker class."""
    TRACKED_TASKS_KEY = "tracked_tasks"

    def __init__(self, task_root):
        """Initialize class.

        Args:
            task_root (TaskRoot): the root task object.
        """
        super(Tracker, self).__init__()
        self.task_root = task_root
        self._tracked_tasks = HostedDataList()

    def iter_tracked_tasks(self, filter=None):
        """Get tasks selected for tracking.

        Args:
            filter (function, BaseFilter or None): filter to apply, if given.

        Yields:
            (Task): tracked tasks.
        """
        with self._tracked_tasks.apply_filter(filter):
            for task in self._tracked_tasks:
                yield task

    @classmethod
    def from_dict(cls, dictionary, task_root):
        """Initialise class from dictionary.

        Args:
            dictionary (dict): the dictionary we're deserializing from.
            task_root (TaskRoot): the root task object.
        """
        tracker = cls(task_root)
        task_paths = dictionary.get(cls.TRACKED_TASKS_KEY, [])
        for task_path in task_paths:
            task = task_root.get_item_at_path(task_path, search_archive=True)
            if task:
                tracker._tracked_tasks.append(task)
                task._is_tracked.set_value(True)
        return tracker

    def to_dict(self):
        """Serialize class as dictionary.

        Returns:
            (dict): the serialized dictionary.
        """
        return {
            self.TRACKED_TASKS_KEY: [
                task.path for task in self._tracked_tasks
            ]
        }
