"""Simple struct to make an attribute mutable, so we can edit it."""


class MutableAttribute(object):
    """Wrapper around a class attribute, to allow us to treat it as mutable."""
    def __init__(self, value):
        """Initialise attribute.

        Args:
            value (variant): value of attribute.
        """
        self._value = value

    @property
    def value(self):
        """Get attribute value.

        Returns:
            value (variant): value of attribute.
        """
        return self._value

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
