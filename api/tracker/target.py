"""Module to define targets for tracked items."""


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
from scheduler.api.utils import fallback_value


class TrackerTargetError(Exception):
    """General exception for tracker target errors."""


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


class BaseTrackerTarget(object):
    """Base class for tracked item targets."""
    def __init__(self, time_period):
        """Initialize class.

        Args:
            time_period (TimePeriod or TimeDelta): time period that target
                is set over (eg. every day, every week, every three days etc.)
        """
        # TODO: update this to allow timedeltas as well? Not sure if wanted
        self._time_period = time_period

    @property
    def time_period(self):
        """Get time period that target is set over.

        Returns:
            (TimePeriod or TimeDelta): time period that target is set over.
        """
        return self._time_period

    def __or__(self, target):
        """Combine this with given target to make a less restrictive target.

        Args:
            target (BaseTrackerTarget): target to combine with.

        Returns:
            (BaseTrackerTarget): target that is met if either the original
                target (self) is met or this new target is met.
        """
        if not isinstance(target, BaseTrackerTarget):
            raise TrackerTargetError(
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
            raise TrackerTargetError(
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
        self._operator = operator
        self._target_value = target_value
        super(BaseTrackerTarget, self).__init__(time_period)

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
        raise TrackerTargetError(
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
        if not subtargets_list:
            raise TrackerTargetError(
                "CompositeTrackerTarget must have at least one subtarget."
            )
        time_period = None
        for target in subtargets_list:
            time_period = fallback_value(time_period, target.time_period)
            if target.time_period != time_period:
                raise Exception(
                    "Cannot combine targets of different time periods "
                    "{0} and {1}".format(target.time_period, time_period)
                )

        super(CompositeTrackerTarget, self).__init__(time_period)
        self._subtargets_list = subtargets_list
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
            raise TrackerTargetError(
                "Unsupported target compositon operator {0}".format(
                    self._compositon_operator
                )
            )

        return boolean_op(
            (target.is_met_by(value) for target in self._subtargets_list)
        )
