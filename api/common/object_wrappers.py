"""Structs to wrap around objects allowing us to edit them."""

from collections import OrderedDict
from collections.abc import Iterable, MutableMapping, MutableSequence
from contextlib import contextmanager
from copy import deepcopy

from scheduler.api.filter import BaseFilter, CustomFilter
from scheduler.api.utils import fallback_value


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
    def __init__(self, *args, **kwargs):
        """Initialize host object."""
        super(_HostObject, self).__init__(*args, **kwargs)
        self._redirected_host = None
        self.set_data = self.set_value

    @property
    def value(self):
        """Value property.

        Returns:
            (variant): underlying data.
        """
        if self._redirected_host is not None:
            return self._redirected_host.value
        return super(_HostObject, self).value

    @property
    def data(self):
        """New name for value.

        Returns:
            (variant): underlying data.
        """
        return self.value

    def set_value(self, value):
        """Set underlying data.

        Args:
            value (variant): new value to set.

        Returns:
            (bool): True if value was changed, else False.
        """
        if self._redirected_host is not None:
            raise HostError("Cannot set value on a redirect host")
        return super(_HostObject, self).set_value(value)

    @property
    def defunct(self):
        """Check if this is defunct.

        Returns:
            (bool): whether or not this host is no longer valid.
        """
        return (self._value is None or self._value.defunct)


class Hosted(object):
    """Base for classes that have a host attribute."""
    def __init__(self, *args, **kwargs):
        """Initialize class.

        Attributes:
            _host (_HostObject or None): host object that hosts this class
                instance as data.
            _paired_data_containers (dict(str,BaseHostedDataContainer)):
                dictionary of attributes of this class that are containers
                of other hosted data, keyed by their 'pairing' id. This is
                used for the 'pairing' framework which ensures that hosted
                data which mutually reference eachother stay up to date with
                each other's edits.
            _driver_paried_data_containers (dict(str,BaseHostedDataContainer)):
                dictionary of paired data containers that must drive their
                pair.
            _driven_paried_data_containers (dict(str,BaseHostedDataContainer)):
                dictionary of paired data containers that must be driven by
                their pair.
        """
        super(Hosted, self).__init__(*args, **kwargs)
        self._host = None
        self._paired_data_containers = {}
        self._driver_paired_data_containers = {}
        self._driven_paired_data_containers = {}

    @property
    def host(self):
        """Get host attribute.

        Returns:
            (_HostObject): host object.
        """
        return self._host

    @property
    def defunct(self):
        """Check if hosted data object is no longer/not yet valid.

        This is here for convenience so that subclasses can reimplement it,
        specifically for cases where they're referencing currently defunct
        hosts, eg. we can specify a planned item is defunct if the tree
        item it references is defunct.

        Returns:
            (bool): whether or not hosted data is defunct.
        """
        return (self._host is None or self._host.data is None)

    def _iter_paired_data_containers(self):
        """Iterate through all paired data containers in this class.

        Yields:
            (_BaseHostedDataContainer): paired data containers in class.
        """
        for container in self._paired_data_containers.values():
            yield container
        for driver_container in self._driver_paired_data_containers.values():
            yield driver_container
        for driven_container in self._driven_paired_data_containers.values():
            yield driven_container

    def _activate(self, host=None):
        """Activate hosted object.

        This needs to be done before the hosted data can be accessed by
        other classes.

        Args:
            host (_HostObject or None): host to activate with. This is
                used when stealing the host of another hosted data
                object, in order to replace it. If not given, we create
                a new host.
        """
        if not self.defunct:
            raise HostError("Cannot activate already active object.")

        if host is not None:
            # if host is given, we steal that host
            if host.data is not None:
                host.data._deactivate()
            host.set_data(self)
            self._host = host
        elif self._host is not None:
            # if host already exists, reactivate it
            if self._host.data is not None:
                self._host.data._deactivate()
            self._host.set_data(self)
        else:
            # if no host is given and none exists, make a new one
            self._host = _HostObject(self)

        # apply pairing
        for container in self._iter_paired_data_containers():
            container._apply_pairing()

    def _deactivate(self):
        """Deactivate hosted object.

        This makes the hosted data defunct so it can no longer be accessed by
        other classes.
        """
        if self.defunct:
            raise HostError("Cannot deactivate already inactive object.")
        self._host.set_data(None)
        for container in self._iter_paired_data_containers():
            container._unapply_pairing()

    def _redirect_host(self, other_host):
        """Redirected this data's host to another host.

        This means the host now points at the data of the new host - it is used
        in edits that merge two Hosted objects together, and it is assumed that
        after this function is run, this hosted object has been removed and
        its relevant data has been merged into the data of the new host.

        Args:
            other_host (_HostObject or None): other host to merge this one into.
                If None, we remove the redirection instead.
        """
        if other_host is not None and other_host._redirected_host is not None:
            # To avoid potential recursion, enforce max one level of redirects
            raise HostError("Cannot redirect host to another redirected host")
        if other_host is None:
            self.host._redirected_host = None
            self.host.set_data(self)
        else:
            self.host.set_data(None)
            self.host._redirected_host = other_host


class _BaseHostedContainer():
    """Base class for classes that hold a hosted object.

    These are for mutable attributes or list or dict attributes in a Hosted
    class that reference instances of other Hosted classes.

    This base class provides the base implementation for the pairing
    framework. The key concept behind this framework is that some classes
    will contain mutual references to eachother (eg. each planned item
    contains an attribute defining the tree item it applies to and each
    tree item contains attribtues listing the items planned for it). To
    avoid constantly needing to define double-updates in the edit classes,
    a hosted container can instead define a connection to another hosted
    container so that updates to one will automatically update the other
    (so eg. changing the tree item attr of a planned item automatically
    removes that planned item from the planned_item list of its old tree
    attribute, and adds it to the list of its new tree attribute).
    """
    def __init__(
            self,
            pairing_id=None,
            parent=None,
            driver=False,
            driven=False,
            *args,
            **kwargs):
        """Initialize.

        Args:
            pairing_id (str or None): if given, this is the id that defines the
                pairing of this container with a container in another hosted
                class. This same id must be passed to the init of that other
                container too.
            parent (Hosted or None): the class this container is an attribute
                of. This is only required for paired containers.
            driver (bool): if True, this class drives its pair (ie. its pair
                cannot mutate itself and can only be updated through updates
                to this container). This requires that the pair is initialized
                with driven=True.
            driven (bool): if True, this class is driven by its pair (see
                above). This requires that its pair is initialized with
                driver=True.
        """
        if pairing_id is not None and parent is None:
            raise HostError(
                "Must pass a parent arg with a pairing_id arg."
            )
        if driven and driver:
            raise HostError(
                "A hosted data container cannot be both driven and a driver."
            )
        super(_BaseHostedContainer, self).__init__(*args, **kwargs)

        self._pairing_id = pairing_id
        self._parent = parent
        self._driver = driver
        self._driven = driven
        self._locked = driven
        if pairing_id is not None:
            parent_dict = self._get_parent_paired_container_dict()
            if pairing_id in parent_dict:
                raise HostError(
                    "Two paired containers with the same parent "
                    "must specify a driver and a driven."
                )
            parent_dict[pairing_id] = self

    @contextmanager
    def _unlock_and_disconnect(self):
        """Temporarily unlock container and disconnect any paired containers."""
        locked = self._locked
        pairing_id = self._pairing_id
        self._locked = False
        self._pairing_id = None
        yield
        self._locked = locked
        self._pairing_id = pairing_id

    @property
    def is_paired(self):
        """Check if this container is paired to another.

        Returns:
            (bool): whether or not container is paired.
        """
        return self._pairing_id is not None

    def _get_parent_paired_container_dict(self):
        """Get dictionary of paired containers that this should be in.

        Returns:
            (dict): the dictionary this should live in.
        """
        if self._driver:
            return self._parent._driver_paired_data_containers
        elif self._driven:
            return self._parent._driven_paired_data_containers
        else:
            return self._parent._paired_data_containers

    def _get_paired_container(self, host):
        """Get the paired container for this item in the given host.

        Args:
            host (_HostObject): host of data that holds the paired
                container.

        Returns:
            (_BaseDataContainer): the paired container.
        """
        if self._driver:
            container_dict = host.data._driven_paired_data_containers
        elif self._driven:
            container_dict = host.data._driver_paired_data_containers
        else:
            container_dict = host.data._paired_data_containers
        container = container_dict.get(self._pairing_id)
        if not isinstance(container, _BaseHostedContainer):
            raise HostError("No valid paired data container found.")
        return container

    def _assert_not_locked(self):
        """Check if container is locked, and raise an error if so."""
        if self._locked:
            raise HostError("Cannot mutate locked data container.")

    def _get_host_object(self, value):
        """Get host object for given value.

        Args:
            value (Hosted, _HostObject or None): value to find host object for.

        Returns:
            (_HostObject): corresponding host object.
        """
        if isinstance(value, Hosted):
            if value.host is None:
                raise HostError("Inactive hosted data cannot be accessed.")
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

    def _add_to_paired_container(self, host):
        """Add this class instance to paired container.

        Args:
            host (_HostObject): host of data whose container we should update.
        """
        container = self._get_paired_container(host)
        with container._unlock_and_disconnect():
            container._add_paired_object(self._parent)

    def _remove_from_paired_container(self, host):
        """Remove this class instance from paired container.

        Args:
            host (_HostObject): host of data whose container we should update.
        """
        container = self._get_paired_container(host)
        with container._unlock_and_disconnect():
            container._remove_paired_object(self._parent)

    def _apply_pairing(self):
        """Add this container's class instance to its paired containers.

        This only should be run during activation of the class instance.
        """
        for host in self._iter_hosts():
            self._add_to_paired_container(host)

    def _unapply_pairing(self):
        """Remove this container's class instance from its paired containers.

        This only should be run during deactivation of the class instance.
        """
        for host in self._iter_hosts():
            self._remove_from_paired_container(host)

    def _iter_hosts(self):
        """Iterate through all hosts in this container.

        Yields:
            (_HostObject): the contained hosts.
        """
        raise NotImplementedError(
            "_iter_hosts must be implemented in subclasses."
        )

    def _add_paired_object(self, hosted_data):
        """Add the paired value to this container.

        Args:
            hosted_data (Hosted): hosted data to add.
        """
        raise NotImplementedError(
            "_add_paired_object must be implemented in subclasses."
        )

    def _remove_paired_object(self, hosted_data):
        """Remove the paired value from this container.

        Args:
            hosted_data (Hosted): hosted data to remove.
        """
        raise NotImplementedError(
            "_remove_paired_object must be implemented in subclasses."
        )


class MutableHostedAttribute(_BaseHostedContainer, BaseObjectWrapper):
    """Wrapper around a _HostObject that allows us to treat it as mutable.

    This is just a mutable attribute around a host object. It is for class
    attributes that are host objects but also need to be editable. For ease,
    any time a class needs to hold a hosted data item as an attribute, it
    should use this class (even if the class doesn't need to mutate the data
    itself).
    """
    def __init__(
            self,
            value,
            name=None,
            pairing_id=None,
            parent=None,
            driver=False,
            driven=False):
        """Initialise attribute.

        Args:
            value (Hosted, _HostObject or None): value of attribute. This can
                either be the host object directly, or the underlying class
                instance that the host object holds (which must be a hosted
                class). For convenience, None values are also allowed.
            name (str or None): name of attribute, if given.
            pairing_id (str or None): if given, this id defines the pairing
                of this container to another container with the same id.
            parent (Hosted or None): the class this is an attribute of. This
                is only required for paired containers.
            driver (bool): whether or not this container drives its pair.
            driven (bool): whether or not this container is driven by its pair.
        """
        value = self._get_host_object(value)
        super(MutableHostedAttribute, self).__init__(
            pairing_id=pairing_id,
            parent=parent,
            driver=driver,
            driven=driven,
            value=value,
            name=name,
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
        self._assert_not_locked()
        value = self._get_host_object(value)
        if self._value != value:
            if self.is_paired:
                self._remove_from_paired_container(self._value)
                self._add_to_paired_container(value)
            self._value = value
            return True
        return False

    def _iter_hosts(self):
        """Iterate through all hosts in this container.

        Yields:
            (_HostObject): the contained hosts.
        """
        if not self.host.defunct:
            yield self.host

    def _add_paired_object(self, hosted_data):
        """Add the paired value to this container.

        Args:
            hosted_data (Hosted): hosted data to add.
        """
        if self.value is None:
            self.set_value(hosted_data)

    def _remove_paired_object(self, hosted_data):
        """Remove the paired value from this container.

        Args:
            hosted_data (Hosted): hosted data to remove.
        """
        if self.value == hosted_data:
            self.set_value(None)


class HostedDataList(_BaseHostedContainer, MutableSequence):
    """List class for storing hosted data by _HostObjects.

    Any class that need to store a list of hosted data objects should do
    so in this container, so it keeps up to date with any changes to the
    hosted data.
    """
    def __init__(
            self,
            internal_list=None,
            pairing_id=None,
            parent=None,
            filter=None,
            driver=False,
            driven=False):
        """Initialize.

        Args:
            internal_list (list or None): if given, use this to populate the
                internal list.
            pairing_id (str or None): if given, this id defines the pairing
                of this container to another container with the same id.
            parent (Hosted or None): the class this is an attribute
                of. This is only required for paired containers.
            filter (function): additional filter applied to list to ignore
                data in specific cases.
            driver (bool): whether or not this container drives its pair.
            driven (bool): whether or not this container is driven by its pair.
        """
        super(HostedDataList, self).__init__(
            pairing_id=pairing_id,
            parent=parent,
            driver=driver,
            driven=driven,
        )
        self._list = list()
        self._reverse_sort_key = (lambda _: 0)
        self._filter = filter
        if not isinstance(filter, BaseFilter):
            self._filter = CustomFilter(filter)
        self._iter_hosts = self._iter_filtered

        # populate internal list
        if internal_list is not None:
            for item in internal_list:
                self.append(item)

    @contextmanager
    def apply_filter(self, filter=None):
        """Temporarily apply filter (on top of any current filters).

        Args:
            filter (function, BaseFilter or None): filter to apply.
        """
        if not isinstance(filter, BaseFilter):
            filter = CustomFilter(filter)
        old_filter = self._filter
        self._filter &= filter
        try:
            yield
        finally:
            self._filter = old_filter

    def get_filter(self):
        """Get filter to apply to this class from list of filters.

        Returns:
            (BaseFilter): filter class, which take in a single arg
                return True or False to determine whether it should be
                considered part of the list or filtered out.
        """
        return self._filter

    def set_filter(self, filter):
        """Set filter as current filter.

        Args:
            filter (function or BaseFilter): filter to set.
        """
        if not isinstance(filter, BaseFilter):
            filter = CustomFilter(filter)
        self._filter = filter

    def add_filter(self, filter):
        """Add filters to current filtering functions.

        Args:
            filter (function or BaseFilter): filter to add.
        """
        if not isinstance(filter, BaseFilter):
            filter = CustomFilter(filter)
        self._filter &= filter

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
            if not host.defunct and self._filter(host.data):
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
            if not host.defunct and self._filter(host.data):
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
            index (int or slice): index or slice to query.
        """
        if isinstance(index, slice):
            return [v.data for v in list(self._iter_filtered())[index]]

        for i, host in enumerate(self._iter_filtered(reverse=(index < 0))):
            if (index >= 0 and index == i) or (index < 0 and index == -1 - i):
                return host.data
        raise IndexError(
            "Index {0} is outside range of HostedDataList".format(index)
        )

    def __delitem__(self, index):
        """Delete item at index of filtered list.

        Args:
            index (int or slice): index or slice to delete.
        """
        self._assert_not_locked()
        if isinstance(index, slice):
            indexes_and_values = list(self._iter_filtered_with_old_index())
            for old_index, value in indexes_and_values[index]:
                del self._list[old_index]
                if self.is_paired:
                    self._remove_from_paired_container(value)
            return

        iterable = enumerate(
            self._iter_filtered_with_old_index(reverse=(index < 0))
        )
        for i, (old_index, value) in iterable:
            if (index >= 0 and index == i) or (index < 0 and index == -1 - i):
                del self._list[old_index]
                if self.is_paired:
                    self._remove_from_paired_container(value)
                return
        raise IndexError(
            "Index {0} is outside range of HostedDataList".format(index)
        )

    def __setitem__(self, index, value):
        """Set item at index to value.

        Args:
            index (int or slice): index or slice to set.
            value (Hosted, _HostObject, None or list): value to set, or list
                of values if index is a slice.
        """
        self._assert_not_locked()
        if isinstance(index, slice):
            if not isinstance(value, Iterable):
                raise TypeError("Can only assign an iterable with a slice")
            old_indexes_and_values = list(
                self._iter_filtered_with_old_index()
            )[index]
            length = len(old_indexes_and_values)
            if len(value) == length:
                for (i, old_v), v in zip(old_indexes_and_values, value):
                    v = self._get_host_object(v)
                    self._list[i] = v
                    if self.is_paired:
                        self._remove_from_paired_container(old_v)
                        self._add_to_paired_container(v)
                return
            if fallback_value(index.step, 1) != 1:
                raise ValueError(
                    "Attempting to assign sequence of size {0} to extended "
                    "slice of size {1}".format(len(value), length)
                )
            # If splice has step 1, just replace from starting index
            start = fallback_value(index.start, 0)
            for i, old_v in old_indexes_and_values:
                del self._list[i]
                if self.is_paired:
                    self._remove_from_paired_container(old_v)
            if -length < start < length:
                index_to_add_at, _ = old_indexes_and_values[start]
            elif start < 0:
                index_to_add_at = 0
            else:
                index_to_add_at = len(self._list)
            for v in reversed(value):
                self._list.insert(index_to_add_at, self._get_host_object(v))
                if self.is_paired:
                    self._add_to_paired_container(v)
            return

        value = self._get_host_object(value)
        iterable = enumerate(
            self._iter_filtered_with_old_index(reverse=(index < 0))
        )
        for i, (old_index, old_value) in iterable:
            if (index >= 0 and index == i) or (index < 0 and index == -1 - i):
                self._list[old_index] = value
                if self.is_paired:
                    self._remove_from_paired_container(old_value)
                    self._add_to_paired_container(value)
                return
        raise IndexError(
            "Index {0} is outside range of HostedDataList".format(index)
        )

    def __str__(self):
        """Get string representation of list.

        Returns:
            (str): string repr.
        """
        return str(self._list)

    def __str__(self):
        """Get string representation of list.

        Returns:
            (str): string repr.
        """
        return "HostedDataList(" + str(self._list) + ")"

    def insert(self, index, value):
        """Insert given value at given index into list.

        Args:
            index (int): value to insert at.
            value (Hosted, _HostObject or None): value to set):
        """
        self._assert_not_locked()
        value = self._get_host_object(value)
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
        if self.is_paired:
            self._add_to_paired_container(value)

    def sort(self, key=None, reverse=False, key_by_host=False):
        """Sort list by given key.

        Args:
            key (function or None): function to sort by.
            reverse (bool): if True, sort in reverse.
            key_by_host (bool): if True, the key function applies to the
                host objects rather than the data. This is needed for reverse
                sorting functionality so we can correctly sort defunct hosts.
        """
        default_value = -1
        for host in self._iter_filtered():
            default_value = key(host.data)
            break
        new_key = key
        if not key_by_host:
            def new_key(host):
                if host.defunct:
                    return default_value
                return key(host.data)

        reverse_key_list = [(i, v) for i, v in enumerate(self._list)]
        def reverse_sort_key(host):
            for i, v in reverse_key_list:
                if v == host:
                    return i
            return -1
        self._reverse_sort_key = reverse_sort_key

        self._list.sort(key=new_key, reverse=reverse)

    def get_reverse_key(self):
        """Get reverse key, used for undoing the most recent sort.

        Returns:
            (function): key to undo the previous sort. This key must be
                applied to host objects rather than to the data.
        """
        return self._reverse_sort_key

    def _add_paired_object(self, hosted_data):
        """Add the paired value to this container.

        Args:
            hosted_data (Hosted): hosted data to add.
        """
        if hosted_data not in self:
            self.append(hosted_data)

    def _remove_paired_object(self, hosted_data):
        """Remove the paired value from this container.

        Args:
            hosted_data (Hosted): hosted data to remove.
        """
        if hosted_data in self:
            self.remove(hosted_data)

    def __copy__(self):
        """Return shallow copy of object.

        Returns:
            (HostedDataList): shallow copy of self.
        """
        return HostedDataList(
            self._list,
            pairing_id=self._pairing_id,
            parent=self._parent,
            filter=self._filter,
            driver=self._driver,
            driven=self._driven,
        )

    def __deepcopy__(self):
        """Return deep copy of object.

        Returns:
            (HostedDataList): deep copy of self.
        """
        # NOTE: not sure how deepcopys will work with hosted objects
        # so will need to test if I ever use this
        return HostedDataList(
            [deepcopy(item) for item in self._list],
            pairing_id=self._pairing_id,
            parent=self._parent,
            filter=self._filter,
            driver=self._driver,
            driven=self._driven,
        )


class HostedDataDict(_BaseHostedContainer, MutableMapping):
    """Dict class for keying data by _HostObjects.

    Any class that needs to store a dict (or ordered dict) of hosted data
    objects should do so in this container, so it keeps up to date with
    any changes to the hosted data.
    """
    def __init__(
            self,
            internal_dict=None,
            host_keys=True,
            host_values=False,
            pairing_id=None,
            parent=None,
            key_value_func=None,
            filter=None,
            driver=False,
            driven=False):
        """Initialize.

        Args:
            internal_dict (dict or None): if given, use this to populate the
                internal dict.
            host_keys (bool): if True, keys are hosted.
            host_values (bool): if True, values are hosted.
            pairing_id (str or None): if given, this id defines the pairing
                of this container to another container with the same id.
            parent (Hosted or None): the class this is an attribute
                of. This is only required for paired containers.
            key_value_func (function or None): function to get key and value of
                a hosted data object that's being added to this class, needed
                for pairing functionality.
            filter (function or None): additional filter for data. Must accept
                key and value as args and return True or False.
            driver (bool): whether or not this container drives its pair.
            driven (bool): whether or not this container is driven by its pair.
        """
        if not host_keys and not host_values:
            raise HostError(
                "HostedDataDict must use hosted data for keys or values"
            )
        if pairing_id is not None and self._key_value_func is None:
            raise HostError(
                "Paired HostedDataDicts must have a key_value_func"
            )
        super(HostedDataDict, self).__init__(
            pairing_id=pairing_id,
            parent=parent,
            driver=driver,
            driven=driven,
        )
        self._keys_are_hosted = host_keys
        self._values_are_hosted = host_values
        self._key_list = []
        self._value_list = []
        self._key_value_func = key_value_func
        self._filter = filter
        if not isinstance(filter, BaseFilter):
            self._filter = CustomFilter(filter)

        # populate internal dict
        if internal_dict is not None:
            for key, value in internal_dict.items():
                self[key] = value

    @contextmanager
    def apply_filter(self, filter=None):
        """Temporarily apply filter (on top of any current filters).

        Args:
            filter (function, BaseFilter or None): filter to apply.
        """
        if not isinstance(filter, BaseFilter):
            filter = CustomFilter(filter)
        old_filter = self._filter
        self._filter &= filter
        try:
            yield
        finally:
            self._filter = old_filter

    def get_filter(self):
        """Get filter to apply to this class from list of filters.

        Returns:
            (BaseFilter): filter class, which take in a single arg
                return True or False to determine whether it should be
                considered part of the list or filtered out.
        """
        return self._filter

    def set_filter(self, filter):
        """Set filter as current filter.

        Args:
            filter (function or BaseFilter): filter to set.
        """
        if not isinstance(filter, BaseFilter):
            filter = CustomFilter(filter)
        self._filter = filter

    def add_filter(self, filter):
        """Add filters to current filtering functions.

        Args:
            filter (function or BaseFilter): filter to add.
        """
        if not isinstance(filter, BaseFilter):
            filter = CustomFilter(filter)
        self._filter &= filter

    def _iter_filtered(self, reverse=False):
        """Iterate through filtered dict.

        Args:
            reverse (bool): if True, iterate in reverse.

        Yields:
            (variant or _HostObject): the valid keys.
            (variant or _HostObject): the valid values.
        """
        key_list = self._key_list
        value_list = self._value_list
        if reverse:
            key_list = reversed(key_list)
            value_list = reversed(value_list)
        for key, value in zip(key_list, value_list):
            if ((self._values_are_hosted and value.defunct)
                    or (self._keys_are_hosted and key.defunct)):
                continue
            key_data = key.data if self._keys_are_hosted else key
            value_data = value.data if self._values_are_hosted else value
            if not self._filter(key_data, value_data):
                continue
            yield key, value

    def _iter_filtered_with_old_index(self):
        """Iterate through filtered dict.

        Yields:
            (int): index of key, value in _key_list and _value_list.
            (variant or _HostObject): the valid keys.
            (variant or _HostObject): the valid values.
        """
        for i, (k, v) in enumerate(zip(self._key_list, self._value_list)):
            if ((self._values_are_hosted and v.defunct)
                    or (self._keys_are_hosted and k.defunct)):
                continue
            key_data = k.data if self._keys_are_hosted else k
            value_data = v.data if self._values_are_hosted else v
            if not self._filter(key_data, value_data):
                continue
            yield i, k, v

    def __iter__(self):
        """Iterate through filtered keys.

        Yields:
            (variant or Hosted): the valid keys (as data rather than host
                objects, since this method is accessed externally).
        """
        for k, _ in self._iter_filtered():
            if self._keys_are_hosted:
                yield k.data
            else:
                yield k

    def __reversed__(self):
        """Iterate backwards through filtered keys.

        Yields:
            (BaseDateTimeWrapper): the keys.
        """
        for k, _ in self._iter_filtered(reverse=True):
            if self._keys_are_hosted:
                yield k.data
            else:
                yield k

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
            if ((self._keys_are_hosted and k.data == key)
                    or (not self._keys_are_hosted and k == key)):
                return v.data if self._values_are_hosted else v
        raise KeyError(
            "No valid item at key {0} in HostedDataDict".format(key)
        )

    def __delitem__(self, key):
        """Delete item at key of filtered list.

        Args:
            key (variant or _Hosted): key to delete.
        """
        self._assert_not_locked()
        for i, k, v in self._iter_filtered_with_old_index():
            if ((self._keys_are_hosted and k.data == key)
                    or (not self._keys_are_hosted and k == key)):
                del self._key_list[i]
                del self._value_list[i]
                if self.is_paired:
                    if self._keys_are_hosted:
                        self._remove_from_paired_container(k)
                    if self._values_are_hosted:
                        self._remove_from_paired_container(v)
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
        self._assert_not_locked()
        if self._values_are_hosted:
            value = self._get_host_object(value)
        for i, k, v in self._iter_filtered_with_old_index():
            if ((self._keys_are_hosted and k.data == key)
                    or (not self._keys_are_hosted and k == key)):
                self._value_list[i] = value
                if self.is_paired and self._values_are_hosted:
                    self._remove_from_paired_container(v)
                    self._add_to_paired_container(value)
                return
        # if key not in list, add new one
        if self._keys_are_hosted:
            key = self._get_host_object(key)
            if key.defunct:
                raise HostError(
                    "Cannot set defunct hosted data {0} as key in "
                    "HostedDataDict".format(key)
                )
        self._key_list.append(key)
        self._value_list.append(value)
        if self.is_paired:
            if self._keys_are_hosted:
                self._add_to_paired_container(key)
            if self._values_are_hosted:
                self._add_to_paired_container(value)

    def __str__(self):
        """Get string representation of dict.

        Returns:
            (str): string repr.
        """
        string = ", ".join([
            "{0}:{1}".format(key, value)
            for key, value in zip(self._key_list, self._value_list)
        ])
        return "{" + string + "}"

    def __repr__(self):
        """Get string representation of dict.

        Returns:
            (str): string repr.
        """
        string = ", ".join([
            "{0}:{1}".format(key, value)
            for key, value in zip(self._key_list, self._value_list)
        ])
        return "HostedDataDict({" + string + "})"

    def _iter_hosts(self):
        """Iterate through all hosts in this container.

        Yields:
            (_HostObject): the contained hosts.
        """
        for key, value in self._iter_filtered():
            if self._keys_are_hosted:
                yield key
            if self._values_are_hosted:
                yield value

    def _add_paired_object(self, hosted_data):
        """Add the paired value to this container.

        Args:
            hosted_data (Hosted): hosted data to add.
        """
        key, value = self._key_value_func(hosted_data)
        if key not in self:
            self[key] = value

    def _remove_paired_object(self, hosted_data):
        """Remove the paired value from this container.

        Args:
            hosted_data (Hosted): hosted data to remove.
        """
        key, _ = self._key_value_func(hosted_data)
        if key in self:
            del self[key]

    def move_to_end(self, key, last=True):
        """Move key, value to one end of dict.

        Args:
            key (variant or Hosted): key to move.
            last (bool): if true, move to last element of dict, otherwise
                move to start of dict.
        """
        self._assert_not_locked()
        for i, k, _ in self._iter_filtered_with_old_index():
            if ((self._keys_are_hosted and k.data == key)
                    or (not self._keys_are_hosted and k == key)):
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

    def __copy__(self):
        """Return shallow copy of object.

        Returns:
            (HostedDataList): shallow copy of self.
        """
        return HostedDataDict(
            OrderedDict(zip(self._key_list, self._value_list)),
            host_keys=self._keys_are_hosted,
            host_values=self._values_are_hosted,
            pairing_id=self._pairing_id,
            parent=self._parent,
            key_value_func=self._key_value_func,
            filter=self._filter,
            driver=self._driver,
            driven=self._driven,
        )

    def __deepcopy__(self):
        """Return deep copy of object.

        Returns:
            (HostedDataList): deep copy of self.
        """
        # NOTE: not sure how deepcopys will work with hosted objects
        # so will need to test if I ever use this
        internal_dict = OrderedDict(
            zip(
                [deepcopy(key) for key in self._key_list],
                [deepcopy(value) for value in self._value_list],
            )
        )
        return HostedDataDict(
            internal_dict,
            host_keys=self._keys_are_hosted,
            host_values=self._values_are_hosted,
            pairing_id=self._pairing_id,
            parent=self._parent,
            key_value_func=self._key_value_func,
            filter=self._filter,
            driver=self._driver,
            driven=self._driven,
        )
