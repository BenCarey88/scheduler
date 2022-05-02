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


class HostObject(BaseObjectWrapper):
    """Wrapper that hosts another object.

    This is intended to be used by any class that can be edited to become a
    different class (eg. Task and TaskCategory). The concept is that each such
    class instance will be 'hosted' by one of these HostObject wrappers. We
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
        return (self._value == None)


class _Hosted():
    """Empty class used to determine if a class has been hosted or not."""


def host_class_decorator(class_):
    """Decorator for a class to give its instances host attributes."""
    class DecoratedClass(class_, _Hosted):

        def __init__(self, *args, **kwargs):
            """Initialize class."""
            super(DecoratedClass, self).__init__(*args, **kwargs)
            self._host = HostObject(self)

        @property
        def host(self):
            """Get host attiribute.

            Returns:
                (HostObject): host object.
            """
            return self._host

        def _switch_host(self, new_host):
            """Switch out host to a different host.

            This should only be used by edit classes that are replacing some
            class instance with an instance of class. We then need to ensure
            that the class instance whose host we're stealing is not accessed
            again as it should be considered deleted once its host is gone.
            Similarly, this item's old host should never be accessed again, as
            conceptually hosts should be in one-to-one correspondence with
            their data.

            Args:
                new_host (HostObject): new host to use.
            """
            self._host.set_data(None)
            self._host = new_host
            new_host.set_data(self)

    return DecoratedClass


class MutableHostedAttribute(BaseObjectWrapper):
    """Wrapper around a HostObject that allows us to treat it as mutable.

    This is just a mutable attribute around a host object. It is for class
    attributes that are host objects but also need to be editable.
    """
    def __init__(self, value, name=None):
        """Initialise attribute.

        Args:
            value (HostObject or _Hosted): value of attribute. This can either
                be the host object directly, or the underlying class instance
                that the host object holds (which must be a hosted class)
            name (str or None): name of attribute, if given.
        """
        if isinstance(value, HostObject):
            value = value
        elif isinstance(value, _Hosted):
            value = value.host
        else:
            raise HostError(
                "Cannot create MutableHostedAttribute for unhosted class "
                "instance {0}".format(value.__class__.__name__)
            )
        super(MutableHostedAttribute, self).__init__(
            value,
            name
        )

    @property
    def host(self):
        """Get attribute host. This is just the MutableAttribute value.

        Returns:
            (HostObject): value of attribute.
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
            value (HostObject or variant): new value to set. If a host object
                is given, we set it directly. Otherwise we set the host object
                to be the host of the new value. Note that this doesn't mutate
                this class's existing HostObject - that can only be done
                through edits on the host's underlying data.

        Returns:
            (bool): True if value was changed, else False.
        """
        if isinstance(value, HostObject):
            if self.host == value:
                return False
            self._host = value
        else:
            if self.value == value:
                return False
            self._host = value.host
        return True
