"""Module to define targets for tracked items."""


from scheduler.api.enums import (
    CompositionOperator,
    OrderedStringEnum,
    TimePeriod,
    TrackedValueType,
)
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


"""Dict of serializable target classes"""
_SERIALIZABLE_TARGET_CLASSES = {}


# TODO: this method is copied from filter serialization. Might be neat
# to make some utils that do this sort of registration in general case
# and import them for these modules
def register_serializable_target(class_name):
    """Create decorator to register a target as serializable.

    Args:
        class_name (str): name to register under.

    Returns:
        (function): the class decorator to register the target class.
    """
    def register_class_decorator(target_class):
        if class_name in _SERIALIZABLE_TARGET_CLASSES:
            raise TrackerTargetError(
                "Cannot register multiple targets with name {0}".format(
                    class_name
                )
            )
        _SERIALIZABLE_TARGET_CLASSES[class_name] = target_class
        target_class._TARGET_CLASS_NAME = class_name
        return target_class
    return register_class_decorator


def target_from_dict(dict_repr):
    """Get target class instance from dictionary representation.

    Args:
        dict_repr (dict): dictionary representation of class.

    Returns:
        (BaseTrackerTarget or None): the target class, if found.
    """
    target_class_name = dict_repr.get(BaseTrackerTarget._TARGET_CLASS_NAME_KEY)
    target_class = _SERIALIZABLE_TARGET_CLASSES.get(target_class_name)
    if target_class is not None:
        target = target_class._from_dict(dict_repr)
        return target
    return None


class BaseTrackerTarget(object):
    """Base class for tracked item targets."""
    _TARGET_CLASS_NAME_KEY = "target_class"
    _TARGET_CLASS_NAME = None

    def __init__(self, time_period, value_type):
        """Initialize class.

        Args:
            time_period (TimePeriod or TimeDelta): time period that target
                is set over (eg. every day, every week, every three days etc.)
            value_type (TrackedValueType): value type this target is set for.
        """
        # TODO: update this to allow timedeltas as well? Not sure if wanted
        self._time_period = time_period
        self._value_type = value_type

    @property
    def time_period(self):
        """Get time period that target is set over.

        Returns:
            (TimePeriod or TimeDelta): time period that target is set over.
        """
        return self._time_period
    
    @property
    def value_type(self):
        """Get value type that target is set for.

        Returns:
            (TrackedValueType): value type of target.
        """
        return self._value_type

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

    def to_dict(self):
        """Get dict representation, excluding the class key.

        Returns:
            (dict): the serialized dictionary.
        """
        if self._TARGET_CLASS_NAME is not None:
            dict_repr = self._to_dict()
            dict_repr[self._TARGET_CLASS_NAME_KEY] = self._TARGET_CLASS_NAME
            return dict_repr
        raise TrackerTargetError(
            "Target class {0} is unserializable. It needs to be wrapped by "
            "the register_serializable_target decorator to be serialized."
            "".format(self.__class__.__name__)
        )

    @classmethod
    def _from_dict(cls, dictionary):
        """Get class from dict representation (excluding the class key).

        Args:
            dictionary (dict): the dictionary we're deserializing from.
        """
        raise NotImplementedError(
            "_from_dict method must be implemented in BaseTrackerTaarget "
            "subclasses"
        )

    def _to_dict(self):
        """Serialize class as dictionary.

        Returns:
            (dict): the serialized dictionary.
        """
        raise NotImplementedError(
            "to_dict method must be implemented in BaseTrackerTaarget "
            "subclasses"
        )


@register_serializable_target("TrackerTarget")
class TrackerTarget(BaseTrackerTarget):
    """Class defining a target for a tracked item."""
    TIME_PERIOD_KEY = "time_period"
    VALUE_TYPE_KEY = "value_type"
    TARGET_OPERATOR_KEY = "target_operator"
    TARGET_VALUE_KEY = "target_value"

    def __init__(self, time_period, value_type, target_operator, target_value):
        """Initialize target.

        Args:
            time_period (TimePeriod or TimeDelta): time period that target
                is set over (eg. every day, every week, every three days etc.)
            target_operator (TargetOperator): eg. less than or greater than.
            target_value (variant): value to use with operator (eg. if target
                is before 5:30, use operator 'less than' and value 5:30)
        """
        self._target_operator = target_operator
        self._target_value = target_value
        super(BaseTrackerTarget, self).__init__(time_period, value_type)

    def is_met_by(self, value):
        """Check if the given tracked value means this target has been met.

        Args:
            value (variant): a value for the tracked task that this target
                has been set for.

        Returns:
            (bool): whether or not the given value meets the target.
        """
        if self._target_operator == TargetOperator.LESS_THAN_EQ:
            return (value <= self._target_value)
        if self._target_operator == TargetOperator.GREATER_THAN_EQ:
            return (value >= self._target_value)
        raise TrackerTargetError(
            "Target operation not yet defined for operator {0}".format(
                self._target_operator
            )
        )
    
    @classmethod
    def _from_dict(cls, dictionary):
        """Initialise class from dictionary.

        Args:
            dictionary (dict): the dictionary we're deserializing from.

        Returns:
            (TrackerTarget or None): tracker target, if could be deserialized.
        """
        time_period = TimePeriod.from_string(
            dictionary.get(cls.TIME_PERIOD_KEY)
        )
        value_type = TrackedValueType.from_string(
            dictionary.get(cls.VALUE_TYPE_KEY)
        )
        target_op = TargetOperator.from_string(
            dictionary.get(cls.TARGET_OPERATOR_KEY)
        )
        target_value = value_type.do_json_deserialize(
            dictionary.get(cls.TARGET_VALUE_KEY)
        )
        if any((x is None
                for x in [time_period, value_type, target_op, target_value])):
            return None
        return cls(time_period, value_type, target_op, target_value)

    def _to_dict(self):
        """Serialize class as dictionary.

        Returns:
            (dict): the serialized dictionary.
        """
        return {
            self.TIME_PERIOD_KEY: self.time_period,
            self.VALUE_TYPE_KEY: self.value_type,
            self.TARGET_OPERATOR_KEY: self._target_operator,
            self.TARGET_VALUE_KEY: self.value_type.do_json_serialize(
                self._target_value
            ),
        }


@register_serializable_target("CompositeTarget")
class CompositeTrackerTarget(BaseTrackerTarget):
    """Class for combining tracked item targets."""
    SUBTARGETS_KEY = "subtargets"
    COMPOSITION_OPERATOR_KEY = "composition_operator"

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
        value_type = None
        for target in subtargets_list:
            time_period = fallback_value(time_period, target.time_period)
            value_type = fallback_value(value_type, target.value_type)
            if target.time_period != time_period:
                raise Exception(
                    "Cannot combine targets of different time periods "
                    "{0} and {1}".format(target.time_period, time_period)
                )
            if target.value_type != value_type:
                raise Exception(
                    "Cannot combine targets of different value types "
                    "{0} and {1}".format(target.value_type, value_type)
                )

        super(CompositeTrackerTarget, self).__init__(time_period, value_type)
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

    @classmethod
    def _from_dict(cls, dictionary):
        """Initialise class from dictionary.

        Args:
            dictionary (dict): the dictionary we're deserializing from.
        """
        subtargets = [
            TrackerTarget.from_dict(subdict)
            for subdict in dictionary.get(cls.SUBTARGETS_KEY, [])
        ]
        composition_operator = CompositionOperator.from_string(
            dictionary.get(cls.COMPOSITION_OPERATOR_KEY)
        )
        if not subtargets or composition_operator is None:
            return cls(subtargets, composition_operator)

    def _to_dict(self):
        """Serialize class as dictionary.

        Returns:
            (dict): the serialized dictionary.
        """
        return {
            self.
            self.SUBTARGETS_KEY: [
                target.to_dict() for target in self._subtargets_list
            ],
            self.COMPOSITION_OPERATOR_KEY: self._compositon_operator,
        }
