"""Timline container type, for items stored arranged by datetime."""

from collections import OrderedDict
from collections.abc import MutableMapping

from scheduler.api.utils import fallback_value
from scheduler.api.common.date_time import Date, DateTime, Time


class TimelineError(Exception):
    """Exception class for timeline errors."""


class TimelineDict(MutableMapping):
    """Timeline dict for storing objects by date, time or datetime."""
    def __init__(self, internal_dict=None, timeline_type=None):
        """Initialize.

        Args:
            internal_dict (dict or None): if given, fill internal dict from
                given dict.
            timeline_type (class or None): one of Time, Date or DateTime.
                This is the type of date_time object that we use to key items
                by. If None, we set this based on whatever item we first add.
        """
        if timeline_type not in [None, Date, DateTime, Time]:
            raise TimelineError(
                "Timeline type must be Date, Time or DateTime."
            )
        self._timeline_type = timeline_type
        self._key_list = []
        self._value_list = []
        for k, v in (internal_dict or {}).items():
            self[k] = v

    def __iter__(self):
        """Iterate through datetime keys.

        Yields:
            (BaseDateTimeWrapper): the keys.
        """
        for key in self._key_list:
            yield key

    def __len__(self):
        """Get length of filtered dict.

        Returns:
            (int): length of filtered dict.
        """
        return len(self._key_list)

    def __getitem__(self, key):
        """Get item at key.

        Args:
            key (variant): key to query.

        Returns:
            (variant): value at key.
        """
        for k, v in zip(self._key_list, self._value_list):
            if k == key:
                return v
        raise KeyError(
            "No valid item at key {0} in TimelineDict".format(key)
        )

    def __delitem__(self, key):
        """Delete item at key of filtered list.

        Args:
            key (variant or _Hosted): key to delete.
        """
        for i, (k, _) in enumerate(zip(self._key_list, self._value_list)):
            if k == key:
                del self._key_list[i]
                del self._value_list[i]
                return
        raise KeyError(
            "No valid item at key {0} in HostedDataDict".format(key)
        )

    def __setitem__(self, key, value):
        """Set item at key to value.

        Args:
            key (variant or _Hosted): key to set.
            value (Hosted, _HostObject or None): value to set.
        """
        # check timeline type is correct (or set if not set yet)
        if self._timeline_type is None:
            timeline_type = type(key)
            if timeline_type not in [None, Date, DateTime, Time]:
                raise TimelineError(
                    "Key type must be Date, Time or DateTime."
                )
            self._timeline_type = timeline_type
        else:
            if type(key) != self._timeline_type:
                raise TimelineError(
                    "Key type must be {0}.".format(self._timeline_type)
                )

        # add item in at correct place
        for i, k in enumerate(self._key_list):
            if k == key:
                self._value_list[i] = value
                return
            if k > key:
                self._key_list.insert(i, key)
                self._value_list.insert(i, value)
                return
        self._key_list.append(key)
        self._value_list.append(value)

    def __str__(self):
        """Get string representation of list.

        Returns:
            (str): string repr.
        """
        string = ", ".join([
            "{0}:{1}".format(key, value)
            for key, value in zip(self._key_list, self._value_list)
        ])
        return "{" + string + "}"

    def change_time(self, old_datetime, new_datetime):
        """Change item at old datetime to new datetime.

        Args:
            old_datetime (BaseDateTimeWrapper): date or time to change from.
            new_datetime (BaseDateTimeWrapper): date or time to change to.
        """
        if new_datetime in self:
            raise TimelineError(
                "An item at {0} already exists".format(new_datetime)
            )
        item = self[old_datetime]
        del self[old_datetime]
        self[new_datetime] = item

    def latest_key(self):
        """Get latest date/time in timeline.

        Returns:
            (BaseDateTimeWrapper or None): the latest date/time, if
                the timeline is non-empty.
        """
        for date_time in reversed(self._key_list)):
            return date_time
        return None

    def latest_value(self):
        """Get value at latest date/time in timeline.

        Returns:
            (variant or None): the value at latest date/time.
        """
        for value in reversed(self._value_list):
            return value
        return None

    def latest_item(self):
        """Get latest date/time in timeline and corresponding value.

        Returns:
            (BaseDateTimeWrapper or None): the latest date/time, if
                the timeline is non-empty.
            (variant or None): the value at that time.
        """
        for datetime, value in reversed(zip(self._key_list, self._value_list)):
            return datetime, value
        return None, None

    def earliest_key(self):
        """Get earliest date/time in timeline.

        Returns:
            (BaseDateTimeWrapper or None): the earliest date/time, if
                the timeline is non-empty.
        """
        for date_time in self._key_list:
            return date_time
        return None

    def earliest_value(self):
        """Get value at earliest date/time in timeline.

        Returns:
            (variant or None): the value at the earliest date/time.
        """
        for value in self._value_list:
            return value
        return None

    def earliest_item(self):
        """Get earliest date/time in timeline and corresponding value.

        Returns:
            (BaseDateTimeWrapper or None): the earliest date/time, if
                the timeline is non-empty.
            (variant, None): the value at that time.
        """
        for date_time, value in zip(self._key_list, self._value_list):
            return date_time, value
        return None, None


# TODO: would it probably be easier to make this a list instead of an
# ordered dict? I think it probably would.
# Either way, we probably would want it to inherit from MutableSequence
# or MutableMapping
# class Timeline(object):
#     """Timeline container type.

#     This is essentially just a wrapper around an ordered dict that ensures
#     that all keys are date_time objects and that new items get fitted in
#     in the correct place in the timeline relative to the other keys.

#     The internal structure is:
#     {
#         date_time_1: [list of items at date_time_1],
#         date_time_2: [list of items at date_time_2],
#         ...
#     }
#     """
#     def __init__(self, internal_dict=None, timeline_type=None):
#         """Initalize container.

#         Args:
#             internal_dict (OrderedDict or None): internal dictionary of class.
#                 If None, we initialize this as empty.
#             timeline_type (class or None): one of Time, Date or DateTime.
#                 This is the type of date_time object that we use to key items
#                 by. If None, we set this based on whatever item we first add.
#         """
#         if internal_dict:
#             timeline_type = timeline_type or type(
#                 next(iter(internal_dict.keys()))
#             )
#         if timeline_type not in [None, Date, DateTime, Time]:
#             raise TimelineError(
#                 "Timeline type must be Date, Time or DateTime."
#             )
#         internal_dict = fallback_value(internal_dict, OrderedDict())
#         for key, value in internal_dict.items():
#             if not isinstance(key, timeline_type):
#                 raise TimelineError(
#                     "Cannot initialise Timeline object with dictionary "
#                     "containing keys of multiple distinct types."
#                 )
#             if not isinstance(value, list):
#                 raise TimelineError(
#                     "Cannot initialise Timeline object with dictionary "
#                     "containing non-list values."
#                 )
#             if len(value) != len(set(value)):
#                 raise TimelineError(
#                     "Timeline class does not allow duplicate items at the "
#                     "same time."
#                 )
#         self._dict = internal_dict
#         self._timeline_type = timeline_type
#         self.sort_timeline()

#     def check_timeline_order(self):
#         """Check timeline order is correct.

#         Raises:
#             (TimelineError): if timeline order is incorrect.
#         """
#         if not self._dict:
#             return
#         prev_date_time = next(iter(self._dict.keys()))
#         for date_time in self._dict.keys():
#             if date_time < prev_date_time:
#                 raise TimelineError(
#                     "Timeline has incorrect ordering: {0} comes before "
#                     "{1}".format(prev_date_time, date_time)
#                 )

#     def sort_timeline(self):
#         """Sort timeline so order is correct."""
#         new_keys = sorted(list(self._dict.keys()))
#         self._dict = OrderedDict([(key, self._dict[key]) for key in new_keys])

#     def add(self, item, date_time):
#         """Add item at date_time.

#         Args:
#             item (variant): item to add.
#             date_time (BaseDateTimeWrapper): date or time to add item at.
#         """
#         if self._timeline_type is None:
#             if not isinstance(date_time, (Date, DateTime, Time)):
#                 raise TimelineError(
#                     "date_time arg must be Date, Time or DateTime."
#                 )
#             self._timeline_type = type(date_time)
#         elif not isinstance(date_time, self._timeline_type):
#             raise TimelineError(
#                 "Timeline object {0} keys items by {1}, not {2}".format(
#                     str(self),
#                     date_time.__class__.__name__,
#                     self._timeline_type.__name__
#                 )
#             )
#         if date_time in self._dict:
#             if item in self._dict[date_time]:
#                 raise TimelineError(
#                     "Timeline class does not allow duplicate items at the "
#                     "same time (duplication of {0} at time {1})".format(
#                         str(item),
#                         date_time.string()
#                     )
#                 )
#             self._dict[date_time].append(item)
#         else:
#             item_not_added = True
#             for _ in range(len(self._dict)):
#                 key, value = self._dict.popitem(last=False)
#                 if item_not_added and key > date_time:
#                     self._dict[date_time] = [item]
#                     item_not_added = False
#                 self._dict[key] = value
#             if item_not_added:
#                 self._dict[date_time] = [item]

#     def remove_item(self, item, date_time):
#         """Remove given item at given date_time.

#         Args:
#             item (variant): item to remove.
#             date_time (BaseDateTimeWrapper): date or time to remove item at.
#         """
#         try:
#             self._dict[date_time].remove(item)
#         except (KeyError, ValueError):
#             raise TimelineError(
#                 "Item {0} not currently scheduled at time {1}".format(
#                     item,
#                     date_time,
#                 )
#             )
#         if self._dict[date_time] == []:
#             del self._dict[date_time]

#     def change_time(self, item, old_time, new_time):
#         """Change time of given item to new time.

#         Args:
#             item (variant): item to add.
#             date_time (BaseDateTimeWrapper): date or time to change item to.
#         """
#         self.remove_item(item, old_time)
#         self.add(item, new_time)

#     def get(self, date_time):
#         """Get items at date_time.

#         Args:
#             date_time (BaseDateTimeWrapper): date or time to get item at.

#         Returns:
#             (list): list of items at given date_time.
#         """
#         return self._dict.get(date_time)

#     def iter_timeline(self):
#         """Iterate through times and items in order.

#         Yields:
#             (BaseDateTimeWrapper): date_time object.
#             (list): list of all items at that time.
#         """
#         for date_time, item_list in self._dict.items():
#             for item in item_list:
#                 yield date_time, item

#     def iter_items(self):
#         """Iterate through all items in order.

#         Yields:
#             (variant): the items, ordered by time.
#         """
#         for _, item_list in self._dict.items():
#             for item in item_list:
#                 yield item

#     def to_dict(self):
#         """Return internal dictionary.

#         Note that this is NOT the same as serializing the timeline object,
#         as the items in the dictionary may themselves still need to be
#         serialized.

#         Returns:
#             (OrderedDict): internal dict.
#         """
#         return self._internal_dict

#     @classmethod
#     def from_dict(cls, dictionary):
#         """Initialise class from internal dictionary.

#         Note that this is NOT the same as deserializing the timeline object,
#         as the items in the dictionary must be deserialized first before
#         this method can be used.

#         Args:
#             dictionary (OrderedDict): internal dict to initialise with.

#         Returns:
#             (OrderedDict): internal dict.
#         """
#         return cls(dictionary)
