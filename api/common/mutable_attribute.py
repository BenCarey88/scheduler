"""Simple struct to make an attribute mutable, so we can edit it."""


class MutableAttribute(object):
    """Wrapper around a class attribute, to allow us to treat it as mutable."""
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
