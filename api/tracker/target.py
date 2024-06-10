"""Module to define targets for tracked items."""


from scheduler.api.common.date_time import TimeDelta
from scheduler.api.enums import (
    CompositionOperator,
    ItemStatus,
    OrderedStringEnum,
    TimePeriod,
    TrackedValueType as TVT,
)
from scheduler.api.utils import fallback_value


class TrackerTargetError(Exception):
    """General exception for tracker target errors."""


class TargetOperator(OrderedStringEnum):
    """Operators for setting tracked item targets."""
    LESS_THAN_EQ = "at most"
    GREATER_THAN_EQ = "at least"

    @classmethod
    def get_custom_names_dict(cls):
        """Get dict of custom names for operators.
        
        Returns:
            (dict): dict of custom names.
        """
        return {
            cls.LESS_THAN_EQ: {
                TVT.TIME: "by",
            },
            cls.GREATER_THAN_EQ: {
                TVT.TIME: "from",
            },
        }

    @classmethod
    def iter_custom_names(cls, value_type):
        """Iterate through custom names of operators for given value type.

        Args:
            value_type (TrackedValueType): the tracked value type.

        Yields:
            (str): name for target operator that corresponds to the given
                value type.
        """
        for enum, subdict in cls.get_custom_names_dict.items():
            yield subdict.get(value_type, enum.value)

    def get_custom_name(self, value_type):
        """Get custom name of operator for given value type.

        Args:
            value_type (TrackedValueType): the tracked value type.

        Returns:
            (str): name for target operator that corresponds to the given
                value type.
        """
        operator_dict = self.get_custom_names_dict().get(self, {})
        return operator_dict.get(value_type, self.value)

    @classmethod
    def from_custom_name(cls, name):
        """Get enum from custom name.

        Args:
            name (str): custom name.

        Returns
            (TargetOperator or None): target operator, if found.
        """
        custom_names_dict = cls.get_custom_names_dict()
        for enum in TargetOperator:
            if enum.value == name:
                return enum
            subdict = custom_names_dict.get(enum, {})
            for custom_name in subdict.values():
                if custom_name == name:
                    return enum
        return None


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
    TIME_PERIOD_KEY = "time_period"
    VALUE_TYPE_KEY = "value_type"

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
    
    @property
    def is_valid(self):
        """Check if this class defines a valid target.

        Returns:
            (bool): whether or not this target is valid.
        """
        # TODO: use this to check whether value_type is targetable
        return self._time_period is not None and self._value_type is not None

    def get_time_delta(self):
        """Get time delta that target is set over.

        Returns:
            (TimeDelta): timedelta of task.
        """
        if isinstance(self.time_period, TimePeriod):
            return self.time_period.get_time_delta()
        return self.time_period

    def __eq__(self, target):
        """Check if this is equal to other target.
        
        Args:
            target (BaseTrackerTarget): other target.
        """
        raise NotImplementedError("__eq__ must be implemented in subclasses")

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

    def is_met_by_value(self, value):
        """Check if the given tracked value means this target has been met.

        Args:
            value (variant): a value for the tracked task that this target
                has been set for.

        Returns:
            (bool): whether or not the given value meets the target.
        """
        raise NotImplementedError(
            "is_met_by_value method must be implemented in BaseTrackerTaarget "
            "subclasses"
        )

    def is_met_by_task_from_date(self, task, start_date):
        """Check if target is met by task from the given start date.

        Args:
            task (Task): task to check.
            start_date (date): date to start at. We check over all subsequent
                days for the duration of the time period.

        Returns:
            (bool): whether or not the given value meets the target.
        """
        raise NotImplementedError(
            "is_met_by_task_from_date method must be implemented in "
            "BaseTrackerTaarget subclasses"
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


# TODO: is this class needed? We don't really want an empty target
# as the implementation of is_met_by_value would have to either auto-fail
# or auto-succeed, both of which feel wrong
@register_serializable_target("NoTarget")
class NoTarget(BaseTrackerTarget):
    """Class defining an empty target."""
    def _to_dict(self):
        """Serialize class to dict."""
        return {
            self.TIME_PERIOD_KEY: self.time_period,
            self.VALUE_TYPE_KEY: self.value_type,
        }

    @classmethod
    def _from_dict(cls, dictionary):
        """Initialize class from dict."""
        return cls(
            dictionary.get(cls.TIME_PERIOD_KEY),
            dictionary.get(cls.VALUE_TYPE_KEY),
        )

    def __eq__(self, target):
        """Check if this is equal to other target.

        Args:
            target (BaseTrackerTarget): other target.
        """
        return isinstance(target, NoTarget)


@register_serializable_target("TrackerTarget")
class TrackerTarget(BaseTrackerTarget):
    """Class defining a target for a tracked item."""
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
        super(TrackerTarget, self).__init__(time_period, value_type)

    # TODO: need to be more consistent with this stuff - either explicitly
    # allow target_operator and target_value to be None (mention in the
    # __init__ args in that case) OR require them to not be None, in which
    # case most of this is_valid check is unneeded, BUT a similar check
    # needs to be being made on the ui side when the class is called.
    @property
    def is_valid(self):
        """Check if this class defines a valid target.

        Returns:
            (bool): whether or not this target is valid.
        """
        return super(TrackerTarget, self).is_valid and (
            self.target_operator is not None
            and self._target_value is not None
            and isinstance(self._target_value, self._value_type.get_class())
        )

    @property
    def target_operator(self):
        """Get target operator.

        Returns:
            (TargetOperator): target operator.
        """
        return self._target_operator

    @property
    def target_value(self):
        """Get target value.

        Returns:
            (variant): target value.
        """
        return self._target_value
    
    def __eq__(self, target):
        """Check if this is equal to other target.

        Args:
            target (BaseTrackerTarget): other target.
        """
        return (
            isinstance(target, TrackerTarget)
            and self.time_period == target.time_period
            and self.value_type == target.value_type
            and self.target_operator == target.target_operator
            and self.target_value == target.target_value
        )
    
    def __str__(self):
        """Get string representation of target.

        Returns:
            (str): string representation.
        """
        return (
            "TrackerTarget(Period={0}, Type={1}, Operator={2}, Value={3})"
            "".format(
                self.time_period,
                self.value_type,
                self.target_operator,
                self.target_value,
            )
        )

    def is_met_by_value(self, value):
        """Check if the given tracked value means this target has been met.

        Args:
            value (variant or None): a value for the tracked task that this
                target has been set for. Accepts None for ease and autofails.

        Returns:
            (bool): whether or not the given value meets the target.
        """
        if value is None:
            # TODO: should this always be the case? eg. LESS_THAN_EQ
            return False

        if self._target_operator == TargetOperator.LESS_THAN_EQ:
            if self.value_type == TVT.TIME:
                # take into account 24 hour clock for time comparison
                return value.less_than_eq_local(self._target_value)
            return (value <= self._target_value)

        if self._target_operator == TargetOperator.GREATER_THAN_EQ:
            if self.value_type == TVT.TIME:
                # take into account 24 hour clock for time comparison
                return self._target_value.less_than_eq_local(value)
            return (value >= self._target_value)

        raise TrackerTargetError(
            "Target operation not yet defined for operator {0}".format(
                self._target_operator
            )
        )

    # TODO: neaten this and above function? maybe change names
    def is_met_by_task_from_date(self, task, start_date):
        """Check if target is met by task from the given start date.

        Args:
            task (Task): task to check.
            start_date (date): date to start at. We check over all subsequent
                days for the duration of the time period.

        Returns:
            (bool): whether or not the given value meets the target.
        """
        # TODO: for now these two value types can only use TimePeriod.Day
        # we should officially enforce this or create the possibility
        # for eg. week time targets that need target to be met on a given
        # number of days - though probably this should be a separate class
        # that does a kind of MultiTarget (distinct from CompositeTarget)
        if self.value_type == TVT.TIME:
            return self.is_met_by_value(task.get_value_at_date(start_date))
        elif self.value_type == TVT.STATUS:
            return self.is_met_by_value(task.get_status_at_date(start_date))

        combined_value = 0
        end_date = start_date + self.get_time_delta()
        date = start_date
        while date < end_date:
            if self.value_type in (TVT.INT, TVT.FLOAT):
                value = task.get_value_at_date(date)
                if value is not None:
                    combined_value += value
            elif self.value_type == TVT.COMPLETIONS:
                status = task.get_status_at_date(date)
                if status == ItemStatus.COMPLETE:
                    combined_value += 1
            date += TimeDelta(days=1)
        return self.is_met_by_value(combined_value)

    @classmethod
    def _from_dict(cls, dictionary):
        """Initialise class from dictionary.

        Args:
            dictionary (dict): the dictionary we're deserializing from.

        Returns:
            (TrackerTarget or None): tracker target, if could be deserialized.
        """
        value_type = TVT.from_string(
            dictionary.get(cls.VALUE_TYPE_KEY)
        )
        if value_type is None:
            return None
        time_period = TimePeriod.from_string(
            dictionary.get(cls.TIME_PERIOD_KEY)
        )
        target_op = TargetOperator.from_string(
            dictionary.get(cls.TARGET_OPERATOR_KEY)
        )
        target_value = value_type.do_json_deserialize(
            dictionary.get(cls.TARGET_VALUE_KEY)
        )
        if any(x is None for x in [time_period, target_op, target_value]):
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

    def is_met_by_value(self, value):
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
            (target.is_met_by_value(value) for target in self._subtargets_list)
        )

    def is_met_by_task_from_date(self, task, start_date):
        """Check if target is met by task from the given start date.

        Args:
            task (Task): task to check.
            start_date (date): date to start at. We check over all subsequent
                days for the duration of the time period.

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
            (target.is_met_by_task_from_date(task, start_date)
             for target in self._subtargets_list)
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
