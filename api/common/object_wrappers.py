"""Simple structs to wrap around objects allowing us to edit them."""


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
        return (self._value is None)

    def __nonzero__(self):
        """Override bool operator (python 2.x).

        Returns:
            (bool): False if attribute value is None, else True.
        """
        return (self._value is None)


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
