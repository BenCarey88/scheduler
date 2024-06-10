"""Module defining global enums used across various classes."""

from enum import Enum

from .common.date_time import Time, TimeDelta


# TODO: I think the manually defined ordering thing (with tuples) doesn't
# work - either delete this (it's never used) or find a way to make the same
# sort of method work to define other data
class OrderedStringEnum(str, Enum):
    """Base ordered enumerator with string values.

    All string enum classes should inherit from this. It defines an
    ordering on the values based on the order they're written in the
    class definitions, with the first values the smallest.

    If you want to manually define the ordering, you can use tuples
    to define the order values, eg.

    class Color(OrderedStringEnum):
        RED = ("Red", 0)
        BLUE = ("Blue", 1)
        GREEN = ("Green", 2)
    """
    def __new__(cls, *args):
        if len(args) == 1:
            number = len(cls.__members__)
            obj = str.__new__(cls, args[0])
            obj._key_ = number
            return obj
        elif len(args) == 2:
            value, number = args
            obj = str.__new__(cls, value)
            obj._key_ = number
            return obj
        raise Exception(
            "Invalid args to pass to OrderedStringEnum: {0}".format(str(args))
        )

    @classmethod
    def legacy_string_conversions(cls):
        """Get dict of conversions for legacy names.

        Update this in subclasses when an enum name is changed so that we
        can correctly deserialize the old names.

        Returns:
            (dict(str, str)): dictionary of old name keys with the new names
                as the values.
        """
        return {}

    @classmethod
    def from_string(cls, string):
        """Get enum value from the corresponding string.

        Args:
            string (str or None): string to get enum value from.

        Returns:
            (OrderedStringEnum or None): enum value, or None if not found.
        """
        string = cls.legacy_string_conversions().get(string, string)
        try:
            return cls(string)
        except ValueError:
            return None

    @property
    def key(self):
        """Get key for ordering comparisons."""
        return self._key_

    def key_function(self):
        """Get key for ordering comparisons.

        This is the same as the above but no longer implemented as a property.
        """
        return self._key_

    def _assert_comparable(self, other):
        """Assert that the given values are comparable."""
        if (not issubclass(self.__class__, other.__class__)
                or not issubclass(other.__class__, self.__class__)):
            raise Exception(
                "Cannot compare enum values {0} ({1}) and {2} ({3})".format(
                    str(self),
                    self.__class__.__name__,
                    str(other),
                    other.__class__.__name__,
                )
            )

    def __gt__(self, other):
        """Check if this is greater than another enum."""
        self._assert_comparable(other)
        return self.key > other.key

    def __ge__(self, other):
        """Check if this is greater than or equal to another enum."""
        self._assert_comparable(other)
        return self.key >= other.key

    def __lt__(self, other):
        """Check if this is less than another enum."""
        self._assert_comparable(other)
        return self.key < other.key
    
    def __le__(self, other):
        """Check if this is less than or equal to another enum."""
        self._assert_comparable(other)
        return self.key <= other.key

    def __repr__(self):
        """Get string representation of enum."""
        return self.value

    def __str__(self):
        """Get string representation of enum."""
        return self.value

    @classmethod
    def contains(cls, string):
        """Check if enum contains given string."""
        if not isinstance(string, str):
            return False
        for value in cls:
            if value == string:
                return True
        return False

    def next(self, cycle=True):
        """Get the next enum in the class.

        Args:
            cycle (bool): if True, cycle round to start after end.

        Returns:
            (OrderedStringEnum or None): next enum, if found.
        """
        cls = self.__class__
        members = list(cls)
        index = members.index(self) + 1
        if index >= len(members):
            if not cycle:
                return None
            index = 0
        return members[index]

    def prev(self, cycle=True):
        """Get the previous enum in the class.

        Args:
            cycle (bool): if True, cycle round to end after start.

        Returns:
            (OrderedStringEnum or None): previous enum, if found.
        """
        cls = self.__class__
        members = list(cls)
        index = members.index(self) - 1
        if index < 0:
            if not cycle:
                return None
            index = len(members) - 1
        return members[index]


class TimePeriod(OrderedStringEnum):
    """Enum for different time periods."""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

    def get_periodicity_string(self):
        """Get periodicity string.

        Returns:
            (str): string representing the periodicity of the time period.
        """
        return "per {0}".format(self)

    @classmethod
    def from_periodicity_string(cls, string):
        """Get time period from periodicity string.

        Returns:
            (TimePeriod): TimePeriod object.
        """
        return cls(string[4:])

    def get_time_delta(self):
        """Get TimeDelta corresponding to period.

        Returns:
            (TimeDelta): corresponding TimeDelta.        
        """
        return {
            self.DAY: TimeDelta(days=1),
            self.WEEK: TimeDelta(days=7),
            self.MONTH: TimeDelta(months=1),
            self.YEAR: TimeDelta(years=1),
        }.get(self)


class CompositionOperator(OrderedStringEnum):
    """Enum for the two boolean composition operations."""
    AND = "AND"
    OR = "OR"


class TrackedValueType(OrderedStringEnum):
    """Enum for tracker value types."""
    STATUS = "Status"
    COMPLETIONS = "Completions"
    TIME = "Time"
    STRING = "String"
    INT = "Int"
    FLOAT = "Float"
    MULTI = "Multi"

    def get_class(self):
        """Get class corresponding to value type, if one exists:

        Returns:
            (class or None): corresponding class.
        """
        return {
            self.STATUS: ItemStatus,
            self.COMPLETIONS: int,
            self.TIME: Time,
            self.STRING: str,
            self.INT: int,
            self.FLOAT: float,
        }.get(self, None)

    def get_json_serializer(self):
        """Get json serialization function for this tracked_value_type.

        Returns:
            (function or None): method for serializing values of this
                type to a json-compatible dict, if needed.
        """
        return {
            self.TIME: Time.string
        }.get(self, None)

    def get_json_deserializer(self):
        """Get json deserialization function for this tracked_value_type.

        Returns:
            (function or None): method for deserializing values of this
                type from a json-compatible dict, if needed.
        """
        return {
            self.STATUS: ItemStatus.from_string,
            self.TIME: Time.from_string,
        }.get(self, None)

    def do_json_serialize(self, value):
        """Json-serialize the given value.

        Args:
            value (variant): value to serialize.

        Returns:
            (str, int or None): json-serialized value, if possible.
        """
        if self.get_class() is None:
            return None
        if not isinstance(value, self.get_class()):
            return None
        converter = self.get_json_serializer()
        if converter is None:
            return value
        return converter(value)

    def do_json_deserialize(self, value):
        """Json-serialize the given value.

        Args:
            value (str, int or None): value to deserialize.

        Returns:
            (variant or None): json-deserialized value, if possible.
        """
        if value is None:
            return None
        converter = self.get_json_deserializer()
        if converter is None:
            return value
        return converter(value)

    @classmethod
    def from_string(cls, string):
        """Temporary override of from_string for legacy saves."""
        if string == "":
            return cls.STATUS
        return super().from_string(string)


class ItemStatus(OrderedStringEnum):
    """Enum for statuses of items."""
    UNSTARTED = "Unstarted"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"


class ItemSize(OrderedStringEnum):
    """Enum to store size types of items."""
    NONE = ""
    SMALL = "small"
    MEDIUM = "medium"
    BIG = "big"


class ItemImportance(OrderedStringEnum):
    """Enum to store levels of importance for items."""
    NONE = ""
    MINOR = "minor"
    MODERATE = "moderate"
    MAJOR = "major"
    CRITICAL = "critical"


class ItemUpdatePolicy(OrderedStringEnum):
    """Enum defining policies for updating statuses of one item from another.

    Some of these policies are specific for certain use cases, so not all
    are in use in every case.

    Use Cases:
        ScheduledItem -> Task
        PlannedItem -> Task
        PlannedItem <- ScheduledItems (children)
        PlannedItem -> ScheduleItems (children)
        PlannedItem -> PlannedItems (children)

    Policies:
        NO_UPDATE: driving item(s) update has no effect on driven item(s).
        IN_PROGRESS: when driving item(s) is marked as in progress or
            complete, the driven item(s) will be updated to in progress. This
            is the default behaviour.
        COMPLETE: when driving item(s) is marked as in progress or complete,
            driven item(s) will be updated to match. If multiple driving items
            exist, the driven item(s) are marked as complete only if ALL of the
            drivers are complete.
        OVERRIDE: linked item status mirrors original item status directly.
            In this case, all statuses set on the linked item as a result of
            this policy will override any previously set statuses on the item.
            This can only be used when there is only one driving item.
    """
    NO_UPDATE = "No Update"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"
    OVERRIDE = "Override"

    @classmethod
    def legacy_string_conversions(cls):
        """Get dict of conversions for legacy names.

        Returns:
            (dict(str, str)): dictionary of old name keys with the new names
                as the values.
        """
        return {
            "No_Update": "No Update",
            "In_Progress": "In Progress",
        }

    @classmethod
    def get_task_policies(cls):
        """Get policies specific to tasks.

        Returns:
            (list(ItemUpdatePolicy)): list of task update policies.
        """
        return [cls.NO_UPDATE, cls.IN_PROGRESS, cls.COMPLETE]
        # NOTE: we can't currently use the OVERRIDE method here for repeat
        # scheduled item instances (see discussion in schedule edits)

    def get_new_status(self, status_):
        """Get new status to give linked item based on original item status.

        Args:
            status (ItemStatus or list(ItemStatus)): new status or list of new
                statuses for original item(s)

        Returns:
            (ItemStatus or None): new status for linked item, based on status
                of original item(s) and update policy (if one should be set).
        """
        if isinstance(status_, ItemStatus):
            statuses = [status_]
        elif isinstance(status_, list):
            if len(status_) == 0:
                return None
            statuses = status_
        else:
            raise ValueError(
                "get_new_status method requires list or ItemStatus arg"
            )

        if self == self.IN_PROGRESS:
            for status in statuses:
                if status >= ItemStatus.IN_PROGRESS:
                    return ItemStatus.IN_PROGRESS

        elif self == self.COMPLETE:
            all_complete = True
            all_unstarted = True
            for status in statuses:
                if all_complete and status != ItemStatus.COMPLETE:
                    all_complete = False
                if all_unstarted and status != ItemStatus.UNSTARTED:
                    all_unstarted = False
                if not all_complete and not all_unstarted:
                    break
            if all_complete:
                return ItemStatus.COMPLETE
            if not all_unstarted:
                return ItemStatus.IN_PROGRESS

        elif self == self.OVERRIDE:
            if len(statuses) != 1:
                raise Exception (
                    "Override method requires only one linked item"
                )
            return statuses[0]

        return None


class TimeValueUpdates(OrderedStringEnum):
    """Different types of time value update.

    These are used to update the value of a task from a scheduled item.
    """
    START = "Start"
    MIDDLE = "Middle"
    END = "End"

    def get_time(self, start_time, end_time):
        """Get time value defined by enum in given time range.

        Args:
            start_time (Time): start of time range.
            end_time (Time): end of time range.

        Returns:
            (Time): defined time.
        """
        if self == self.START:
            return start_time
        elif self == self.END:
            return end_time
        return (start_time + 0.5 * (end_time - start_time))
