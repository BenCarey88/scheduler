"""Timline container type, for items stored arranged by datetime."""

from collections import OrderedDict

from .date_time import Date, DateTime, Time


class TimelineError(Exception):
    """Exception class for timeline errors."""


class Timeline(object):
    """Timeline container type.

    This is essentially just a wrapper around an ordered dict that ensures
    that all keys are date_time objects and that new items get fitted in
    in the correct place in the timeline relative to the other keys.

    The internal structure is:
    {
        date_time_1: [list of items at date_time_1],
        date_time_2: [list of items at date_time_2],
        ...
    }
    """
    def __init__(self, internal_dict=None, timeline_type=None):
        """Initalize container.

        Args:
            internal_dict (OrderedDict or None): internal dictionary of class.
                If None, we initialize this as empty.
            timeline_type (class or None): one of Time, Date or DateTime.
                This is the type of date_time object that we use to key items
                by. If None, we set this based on whatever item we first add.
        """
        if internal_dict:
            timeline_type = timeline_type or type(
                next(iter(internal_dict.keys()))
            )
        if timeline_type not in [None, Date, DateTime, Time]:
            raise TimelineError(
                "Timeline type must be Date, Time or DateTime."
            )
        for key, value in internal_dict.items():
            if not isinstance(key, timeline_type):
                raise TimelineError(
                    "Cannot initialise Timeline object with dictionary "
                    "containing keys of multiple distinct types."
                )
            if not isinstance(value, list):
                raise TimelineError(
                    "Cannot initialise Timeline object with dictionary "
                    "containing non-list values."
                )
            if len(value) != len(set(value)):
                raise TimelineError(
                    "Timeline class does not allow duplicate items at the "
                    "same time"
                )
        self._dict = internal_dict or OrderedDict()
        self._timeline_type = timeline_type
        self.sort_timeline()

    def check_timeline_order(self):
        """Check timeline order is correct.

        Raises:
            (TimelineError): if timeline order is incorrect.
        """
        if not self._dict:
            return
        prev_date_time = next(iter(self._dict.keys()))
        for date_time in self._dict.keys():
            if date_time < prev_date_time:
                raise TimelineError(
                    "Timeline has incorrect ordering: {0} comes before "
                    "{1}".format(prev_date_time, date_time)
                )

    def sort_timeline(self):
        """Sort timeline so order is correct."""
        new_keys = sorted(list(self._dict.keys()))
        self._dict = OrderedDict([(key, self._dict[key]) for key in new_keys])

    def add(self, item, date_time):
        """Add item at date_time.

        Args:
            item (variant): item to add.
            date_time (BaseDateTimeWrapper): date or time to add item at.
        """
        if self._timeline_type is None:
            if not isinstance(date_time, (Date, DateTime, Time)):
                raise TimelineError(
                    "date_time arg must be Date, Time or DateTime."
                )
            self._timeline_type = type(date_time)
        elif not isinstance(date_time, self._timeline_type):
            raise TimelineError(
                "Timeline object {0} keys items by {1}, not {2}".format(
                    str(self),
                    date_time.__class__.__name__,
                    self._timeline_type.__name__
                )
            )
        if date_time in self._dict:
            if item in self._dict[date_time]:
                raise TimelineError(
                    "Timeline class does not allow duplicate items at the "
                    "same time (duplication of {0} at time {1})".format(
                        str(item),
                        date_time.string()
                    )
                )
            self._dict[date_time].append(item)
        else:
            item_not_added = True
            for _ in range(len(self._dict)):
                key, value = self._dict.popitem(last=False)
                if item_not_added and key > date_time:
                    self._dict[date_time] = [item]
                    item_not_added = False
                self._dict[key] = value
            if item_not_added:
                self._dict[date_time] = [item]

    def remove_item(self, item, date_time):
        """Remove given item at given date_time.

        Args:
            item (variant): item to remove.
            date_time (BaseDateTimeWrapper): date or time to remove item at.
        """
        try:
            self._dict[date_time].remove(item)
        except (KeyError, ValueError):
            raise TimelineError(
                "Item {0} not currently scheduled at time {1}".format(
                    item,
                    date_time,
                )
            )
        if self._dict[date_time] == []:
            del self._dict[date_time]

    def change_time(self, item, old_time, new_time):
        """Change time of given item to new time.

        Args:
            item (variant): item to add.
            date_time (BaseDateTimeWrapper): date or time to change item to.
        """
        self.remove_item(item, old_time)
        self.add(item, new_time)

    def get(self, date_time):
        """Get items at date_time.

        Args:
            date_time (BaseDateTimeWrapper): date or time to get item at.

        Returns:
            (list): list of items at given date_time.
        """
        return self._dict.get(date_time)

    def iter_timeline(self):
        """Iterate through times and items in order.

        Yields:
            (BaseDateTimeWrapper): date_time object.
            (list): list of all items at that time.
        """
        for date_time, item_list in self._dict.items():
            for item in item_list:
                yield date_time, item

    def iter_items(self):
        """Iterate through all items in order.

        Yields:
            (variant): the items, ordered by time.
        """
        for _, item_list in self._dict.items():
            for item in item_list:
                yield item

    def to_dict(self):
        """Return internal dictionary.

        Note that this is NOT the same as serializing the timeline object,
        as the items in the dictionary may themselves still need to be
        serialized.

        Returns:
            (OrderedDict): internal dict.
        """
        return self._internal_dict

    @classmethod
    def from_dict(cls, dictionary):
        """Initialise class from internal dictionary.

        Note that this is NOT the same as deserializing the timeline object,
        as the items in the dictionary must be deserialized first before
        this method can be used.

        Args:
            dictionary (OrderedDict): internal dict to initialise with.

        Returns:
            (OrderedDict): internal dict.
        """
        return cls(dictionary)
