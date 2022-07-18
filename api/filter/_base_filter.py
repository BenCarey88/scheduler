"""Base filter class."""


class FilterError(Exception):
    """Base exception for filter class errors."""


class BaseFilter(object):
    """Base filter class, with function for filtering items in a container."""
    def __init__(self):
        """Initialize."""
        self._filter_builder = CustomFilter
        self._is_valid = True

    def filter_function(self, *args, **kwargs):
        """Filter function.

        Returns:
            (bool): True if item should stay in container, False if it should
                be filtered out.
        """
        return True

    def __call__(self, *args, **kwargs):
        """Call filter function."""
        return self.filter_function(*args, **kwargs)

    def __or__(self, filter_):
        """Combine this with given filter to make a less restrictive filter.

        Args:
            filter_ (BaseFilter): filter to combine with.

        Returns:
            (BaseFilter): filter that keeps an item in list if it satisfies
                either of the two conditions.
        """
        if not filter_ or not self:
            return self._filter_builder()
        if not isinstance(filter_, BaseFilter):
            raise FilterError(
                "Cannot combine filter with non-filter class {0}".format(
                    filter_.__class__.__name__
                )
            )
        def filter_function(*args, **kwargs):
            return (
                self.filter_function(*args, **kwargs)
                or filter_.filter_function(*args, **kwargs)
            )
        return self._filter_builder(filter_function)

    def __and__(self, filter_):
        """Combine this with given filter to make a more restrictive filter.

        Args:
            filter_ (BaseFilter): filter to combine with.

        Returns:
            (BaseFilter): filter that keeps an item in list if it satisfies
                both of the two conditions.
        """
        if not filter_:
            return self
        if not self:
            return filter_
        if not isinstance(filter_, BaseFilter):
            raise FilterError(
                "Cannot combine filter with non-filter class {0}".format(
                    filter_.__class__.__name__
                )
            )
        def filter_function(*args, **kwargs):
            return (
                self.filter_function(*args, **kwargs)
                and filter_.filter_function(*args, **kwargs)
            )
        return self._filter_builder(filter_function)

    def __bool__(self):
        """Override bool operator to return False.

        Returns:
            (bool): whether or not this actually filters anything.
        """
        return self._is_valid

    def __nonzero__(self):
        """Override bool operator to return False (Python 2.x)
        
        Returns:
            (bool): whether or not this actually filters anything.
        """
        return self._is_valid


class FilterFactory(object):
    """Factory to build filter classes around a given function."""
    def __init__(self, filter_class, no_filter=False):
        """Initialize filter factory.

        Args:
            filter_class (class): filter class to build for.
            no_filter (bool): if True, we use this to build an empty filter.
        """
        self._filter_class = filter_class
        self._no_filter = no_filter

    def __call__(self, function=None):
        """Create filter.

        Args:
            function_ (function or None): if given, override filter function
                with this function.

        Returns:
            (BaseFilter): the created filter class.
        """
        if self._no_filter and function is not None:
            raise TypeError("Empty filter does not accept any __init__ args")
        filter_ = self._filter_class()
        if function is None:
            filter_._is_valid = False
        if function is not None:
            filter_.filter_function = function
        return filter_


CustomFilter = FilterFactory(BaseFilter)
