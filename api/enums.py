"""Module defining global enums used across various classes."""

from enum import Enum


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
    def get_values(cls):
        """Get all values for enum."""
        return list(cls.__members__)

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
        NO_UPDATE: diving item(s) update has no effect on driven item(s).
        IN_PROGRESS: when diving item(s) is marked as in progress or
            complete, the driven item(s) will be updated to in progress. This
            is the default behaviour.
        COMPLETE: when driving item(s) is marked as in progress or
            complete, driven item(s) will be updated to match. If multiple
            driving items exist, the driven item(s) be marked as complete only
            if ALL of the drivers are complete.
        OVERRIDE: linked item status mirrors original item(s) status directly.
            In this case, all statuses set on the linked item as a result of
            this policy will override any previously set statuses on the item.
            This can only be used when there is only one driving item.
    """
    NO_UPDATE = "No_Update"
    IN_PROGRESS = "In_Progress"
    COMPLETE = "Complete"
    OVERRIDE = "Override"

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
