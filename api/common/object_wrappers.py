"""Structs to wrap around objects allowing us to edit them."""

from collections.abc import MutableMapping, MutableSequence


class HostError(Exception):
    """Generic exception for host class related errors."""


class BaseObjectWrapper(object):
    """Basic wrapper around an object."""
    def __init__(self, value, name=None):
        """Initialise attribute.

        Args:
            value (variant): value of attribute.
            name (str or None): name of attribute, if given.
        """
        self._value = value
        self._name = name

    @property
    def value(self):
        """Get attribute value.

        Returns:
            (variant): value of attribute.
        """
        return self._value

    @property
    def name(self):
        """Get attribute name.

        Returns:
            (str or None): name of attribute, if given.
        """
        return self._name

    def set_value(self, value):
        """Set value of attribute.

        Args:
            value (variant): new value to set.

        Returns:
            (bool): True if value was changed, else False.
        """
        if self._value == value:
            return False
        self._value = value
        return True

    def __bool__(self):
        """Check whether attribute is None or not.

        Returns:
            (bool): False if attribute value is None, else True.
        """
        return (self.value is not None)

    def __nonzero__(self):
        """Override bool operator (python 2.x).

        Returns:
            (bool): False if attribute value is None, else True.
        """
        return self.__bool__()


class MutableAttribute(BaseObjectWrapper):
    """Wrapper around a class attribute, to allow us to treat it as mutable.

    This is intended to be used for any attributes that a user can edit, so
    we can run AttributeEdits on them.
    """


class _HostObject(BaseObjectWrapper):
    """Wrapper that hosts another object.

    This is intended to be used by any class that can be edited to become a
    different class (eg. Task and TaskCategory). The concept is that each such
    class instance will be 'hosted' by one of these _HostObject wrappers. We
    then call this wrapper the 'host' of the class instance and conversely the
    class instance is called the 'data' of the host.

    Any other class that needs a reference to a hosted data object must hold a
    reference to its host instead and access it through that. Then any edit
    that switches the data to a different class must also ensure that the data
    is switched out in the host, so that the referencing class now holds a
    reference to the new data.
    """
    @property
    def data(self):
        """New name for value.

        Returns:
            (variant): underlying data.
        """
        return self.value

    def set_data(self, value):
        """Set underlying data.

        Args:
            value (variant): new value to set.

        Returns:
            (bool): True if value was changed, else False.
        """
        return self.set_value(value)

    @property
    def defunct(self):
        """Check if this is defunct.

        Returns:
            (bool): whether or not this host is no longer valid.
        """
        return (self._value is None)


class Hosted(object):
    """Base for classes that have a host attribute."""
    def __init__(self, *args, **kwargs):
        """Initialize class."""
        super(Hosted, self).__init__(*args, **kwargs)
        self._host = _HostObject(self)

    @property
    def host(self):
        """Get host attribute.

        Returns:
            (_HostObject): host object.
        """
        return self._host

    @property
    def defunct(self):
        """Check if object hosted data is still valid.

        This is here for convenience so that subclasses can reimplement it,
        specifically for cases where they're referencing currently defunct
        hosts.

        Returns:
            (bool): whether or not hosted data is defunct.
        """
        return False

    def _switch_host(self, new_host):
        """Switch out host to a different host.

        This should only be used by edit classes that are replacing some
        class instance with an instance of another class. We then need to
        ensure that the class instance whose host we're stealing is not
        accessed again as it should be considered deleted once its host is
        gone. Similarly, this item's old host should never be accessed
        again, as conceptually hosts should be in one-to-one correspondence
        with their data.

        Args:
            new_host (_HostObject): new host to use.
        """
        self._host.set_data(None)
        self._host = new_host
        new_host.set_data(self)


class MutableHostedAttribute(BaseObjectWrapper):
    """Wrapper around a _HostObject that allows us to treat it as mutable.

    This is just a mutable attribute around a host object. It is for class
    attributes that are host objects but also need to be editable. For ease,
    any time a class needs to hold a hosted data item as an attribute, it
    should use this class (even if the class doesn't need to mutate the data
    itself).
    """
    def __init__(self, value, name=None):
        """Initialise attribute.

        Args:
            value (Hosted, _HostObject or None): value of attribute. This can
                either be the host object directly, or the underlying class
                instance that the host object holds (which must be a hosted
                class). For convenience, None values are also allowed.
            name (str or None): name of attribute, if given.
        """
        if isinstance(value, Hosted):
            value = value.host
        elif value is None:
            # special unhosted case, allowed for convenience
            value = _HostObject(None)
        elif isinstance(value, _HostObject):
            value = value
        else:
            raise HostError(
                "Cannot create MutableHostedAttribute for instance of "
                "unhosted class {0}".format(value.__class__.__name__)
            )
        super(MutableHostedAttribute, self).__init__(
            value,
            name
        )

    @property
    def host(self):
        """Get attribute host. This is just the MutableAttribute value.

        Returns:
            (_HostObject): attribute host.
        """
        return self._value

    @property
    def value(self):
        """Get attribute value, ie. underlying data of host.

        Returns:
            (variant): value of host data.
        """
        return self.host.data

    def set_value(self, value):
        """Set value of attribute.

        Args:
            value (Hosted or _HostObject): new value to set. If a host object
                is given, we set it directly. Otherwise we set the host object
                to be the host of the new value. Note that this doesn't mutate
                this class's existing _HostObject - that can only be done
                through edits on the host's underlying data.

        Returns:
            (bool): True if value was changed, else False.
        """
        if isinstance(value, Hosted):
            if self.value == value:
                return False
            self._value = value.host
        elif value is None:
            # special unhosted case allowed for convenience
            if self.value is None:
                return False
            self._value = _HostObject(None)
        elif isinstance(value, _HostObject):
            if self.host == value:
                return False
            self._value = value
        else:
            raise HostError(
                "Cannot set MutableHostedAttribute value as instance of "
                "unhosted class {0}".format(value.__class__.__name__)
            )
        return True


class HostedDataList(MutableSequence):
    """List class for storing hosted data by _HostObjects."""
    def __init__(self, *args):
        """Initialize."""
        self._list = list()
        self.extend(list(args))

    def _get_hosted(self, value):
        """Get host to add to list.

        Args:
            value (Hosted, _HostObject or None): value to find host object for.

        Returns:
            (_HostObject): corresponding host object.
        """
        if isinstance(value, Hosted):
            return value.host
        if isinstance(value, _HostObject):
            return value
        elif value is None:
            return _HostObject(None)
        raise HostError(
            "Cannot add unhosted class {0} to HostedDataList".format(
                value.__class__.__name__
            )
        )

    def _iter_filtered(self, reverse=False):
        """Iterate through filtered list.

        Args:
            reverse (bool): if True, iterate in reverse.

        Yields:
            (_HostObject): the valid host objects in the list that
                contain valid data.
        """
        iterable = self._list
        if reverse:
            iterable = reverse(self._list)
        for host in iterable:
            if not host.defunct and not host.data.defunct:
                yield host

    def _iter_filtered_with_old_index(self, reverse=False):
        """Iterate through filtered list.

        Args:
            reverse (bool): if True, iterate in reverse.

        Yields:
            (int): old index. If in reverse, this gives a negative
                index.
            (_HostObject): the valid host objects in the list that
                contain valid data.
        """
        iterable = self._list
        if reverse:
            iterable = reverse(self._list)
        for i, host in enumerate(iterable):
            if not host.defunct and not host.data.defunct:
                if reverse:
                    yield -1 - i, host
                else:
                    yield i, host

    def __len__(self):
        """Get length of filtered list.

        Returns:
            (int): length of filtered list.
        """
        return len(list(self._iter_filtered()))

    def __getitem__(self, index):
        """Get item at index in filtered list.

        Args:
            index (int): index to query.
        """
        for i, host in enumerate(self._iter_filtered(reverse=(index < 0))):
            if (index >= 0 and index == i) or (index < 0 and index == -1 - i):
                return host.data
        raise IndexError(
            "Index {0} is outside range of HostedDataList".format(index)
        )

    def __delitem__(self, index):
        """Delete item at index of filtered list.

        Args:
            index (int): index to delete.
        """
        iterable = enumerate(
            self._iter_filtered_with_old_index(reverse=(index < 0))
        )
        for i, (old_index, _) in iterable:
            if (index >= 0 and index == i) or (index < 0 and index == -1 - i):
                del self._list[old_index]
                return
        raise IndexError(
            "Index {0} is outside range of HostedDataList".format(index)
        )

    def __setitem__(self, index, value):
        """Set item at index to value.

        Args:
            index (int): index to set.
            value (Hosted, _HostObject or None): value to set.
        """
        value = self._get_hosted(value)
        iterable = enumerate(
            self._iter_filtered_with_old_index(reverse=(index < 0))
        )
        for i, (old_index, _) in iterable:
            if (index >= 0 and index == i) or (index < 0 and index == -1 - i):
                self._list[old_index] = value
                return
        raise IndexError(
            "Index {0} is outside range of HostedDataList".format(index)
        )

    def insert(self, index, value):
        """Insert given value at given index into list.

        Args:
            index (int): value to insert at.
            value (Hosted, _HostObject or None): value to set):
        """
        value = self._get_hosted(value)
        iterable = enumerate(
            self._iter_filtered_with_old_index(reverse=(index < 0))
        )
        for i, (old_index, _) in iterable:
            if (index >= 0 and index == i) or (index < 0 and index == -1 - i):
                self._list.insert(old_index, value)
                return
        if index > 0:
            self._list.append(value)
        else:
            self._list.insert(0, value)

    def __str__(self):
        """Get string representation of list.

        Returns:
            (str): string repr.
        """
        return str(self._list)


class HostedDataDict(MutableMapping):
    """Dict class for keying data by _HostObjects."""
    def __init__(self, host_values=False):
        """Initialize.

        Args:
            host_values (bool): if True, values are hosted. Otherwise,
                keys are hosted.
        """
        self._values_are_hosted = host_values
        self._key_list = []
        self._value_list = []

    def _get_hosted(self, value):
        """Get host to add to dict (either as a key or a value).

        Args:
            value (Hosted, _HostObject or None): value to find host object for.

        Returns:
            (_HostObject): corresponding host object.
        """
        if isinstance(value, Hosted):
            return value.host
        if isinstance(value, _HostObject):
            return value
        elif value is None:
            return _HostObject(None)
        raise HostError(
            "Cannot add unhosted class {0} to HostedDataList".format(
                value.__class__.__name__
            )
        )

    def _iter_filtered(self):
        """Iterate through filtered dict.

        Yields:
            (variant or _HostObject): the valid keys.
            (variant or _HostObject): the valid values.
        """
        for key, value in zip(self._key_list, self._value_list):
            if self._values_are_hosted:
                if not value.defunct and not value.data.defunct:
                    yield key, value
            else:
                if not key.defunct and not key.data.defunct:
                    yield key, value

    def _iter_filtered_with_old_index(self):
        """Iterate through filtered dict.

        Yields:
            (int): index of key, value in _key_list and _value_list.
            (variant or _HostObject): the valid keys.
            (variant or _HostObject): the valid values.
        """
        for i, (k, v) in enumerate(zip(self._key_list, self._value_list)):
            if self._values_are_hosted:
                if not v.defunct and not v.data.defunct:
                    yield i, k, v
            elif not k.defunct and not k.data.defunct:
                yield i, k, v

    def __iter__(self):
        """Iterate through filtered keys.

        Yields:
            (variant or Hosted): the valid keys.
        """
        for k, _ in self._iter_filtered():
            if self._values_are_hosted:
                yield k
            else:
                yield k.data

    def __len__(self):
        """Get length of filtered dict.

        Returns:
            (int): length of filtered dict.
        """
        return len(list(self._iter_filtered()))

    def __getitem__(self, key):
        """Get item at key in filtered dict.

        Args:
            key (variant or _Hosted): key to query.

        Returns:
            (variant or _Hosted): value at key.
        """
        for k, v in self._iter_filtered():
            if self._values_are_hosted:
                if k == key:
                    return v.data
            elif k.data == key:
                return v
        raise KeyError(
            "No valid item at key {0} in HostedDataDict".format(key)
        )

    def __delitem__(self, key):
        """Delete item at key of filtered list.

        Args:
            key (variant or _Hosted): key to delete.
        """
        for i, k, _ in self._iter_filtered_with_old_index():
            if self._values_are_hosted:
                if k == key:
                    del self._key_list[i]
                    del self._value_list[i]
                    return
            elif k.data == key:
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
        for i, k, _ in self._iter_filtered_with_old_index():
            if self._values_are_hosted:
                if k == key:
                    self._value_list[i] = self._get_hosted(value)
                    return
            elif k.data == key:
                self._value_list[i] = value
                return
        # if key not in list, add new one
        if self._values_are_hosted:
            value = self._get_hosted(value)
        else:
            key = self._get_hosted(key)
            if key.defunct or key.data.defunct:
                raise HostError(
                    "Cannot set defunct hosted data {0} as key in "
                    "HostedDataDict".format(key)
                )
        self._key_list.append(key)
        self._value_list.append(value)

    def move_to_end(self, key, last=True):
        """Move key, value to one end of dict.

        Args:
            key (variant or Hosted): key to move.
            last (bool): if true, move to last element of dict, otherwise
                move to start of dict.
        """
        for i, k, _ in self._iter_filtered_with_old_index():
            if self._values_are_hosted:
                if k == key:
                    break
            elif k.data == key:
                break
        else:
            raise KeyError(
                "No valid item at key {0} in HostedDataDict".format(key)
            )
        if last:
            self._key_list.append(self._key_list.pop(i))
            self._value_list.append(self._value_list.pop(i))
        else:
            self._key_list.insert(0, self._key_list.pop(i))
            self._value_list.insert(0, self._value_list.pop(i))

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
