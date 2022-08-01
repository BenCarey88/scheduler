"""Base filter class."""


class FilterError(Exception):
    """Base exception for filter class errors."""


"""Dict of serializable filter classes"""
_SERIALIZABLE_FILTER_CLASSES = {}


def register_serializable_filter(class_name):
    """Create decorator to register a filter as serializable.

    Args:
        class_name (str): name to register under.

    Returns:
        (function): the class decorator to register the filter class.
    """
    def register_class_decorator(filter_class):
        if class_name in _SERIALIZABLE_FILTER_CLASSES:
            raise FilterError(
                "Cannot register multiple filters with name {0}".format(
                    class_name
                )
            )
        _SERIALIZABLE_FILTER_CLASSES[class_name] = filter_class
        filter_class._FILTER_CLASS_NAME = class_name
        return filter_class
    return register_class_decorator


def filter_from_dict(dict_repr):
    """Get filter class instance from dictionary representation.

    Args:
        dict_repr (dict): dictionary representation of class.

    Returns:
        (BaseFilter or None): the filter class, if found.
    """
    filter_class = dict_repr.get(BaseFilter._FILTER_CLASS_NAME_KEY)
    if filter_class is not None:
        return filter_class._from_dict(dict_repr)
    return None


class BaseFilter(object):
    """Base filter class, with function for filtering items in a container."""
    _FILTER_CLASS_NAME_KEY = "filter_class"
    _FILTER_CLASS_NAME = None

    def __init__(self):
        """Initialize."""
        self._composite_filter_class = CompositeFilter
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
        # if one filter is the empty filter, return the empty filter
        if not filter_ or not self:
            return self._composite_filter_class()
        if not isinstance(filter_, BaseFilter):
            raise FilterError(
                "Cannot combine filter with non-filter class {0}".format(
                    filter_.__class__.__name__
                )
            )
        # create composite filter from the two filters
        subfilters_list = []
        for f in (self, filter_):
            if (isinstance(f, CompositeFilter)
                    and f._compositon_operator == CompositeFilter.OR):
                subfilters_list.append(f._subfilters_list)
            else:
                subfilters_list.append(f)
        return self._composite_filter_class(
            subfilters_list,
            CompositeFilter.OR,
        )

    def __and__(self, filter_):
        """Combine this with given filter to make a more restrictive filter.

        Args:
            filter_ (BaseFilter): filter to combine with.

        Returns:
            (BaseFilter): filter that keeps an item in list if it satisfies
                both of the two conditions.
        """
        # if either filter is empty, return the other
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
        # create composite filter from the two filters
        subfilters_list = []
        for f in (self, filter_):
            if (isinstance(f, CompositeFilter)
                    and f._compositon_operator == CompositeFilter.AND):
                subfilters_list.append(f._subfilters_list)
            else:
                subfilters_list.append(f)
        return self._composite_filter_class(
            subfilters_list,
            CompositeFilter.AND,
        )

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

    def to_dict(self):
        """Return dictionary representation of class.

        Returns:
            (dict): dictionary representation.
        """
        if self._FILTER_CLASS_NAME is not None:
            dict_repr = self._get_dict_repr()
            dict_repr[self._FILTER_CLASS_NAME_KEY] = self._FILTER_CLASS_NAME
            return dict_repr
        raise FilterError(
            "Filter class {0} is unserializable. It needs to be wrapped by "
            "the register_serializable_filter decorator to be serialized."
            "".format(self.__class__.__name__)
        )

    def _to_dict(self):
        """Get dict representation, excluding the class key.

        Returns:
            (dict): dictionary representation.
        """
        raise NotImplementedError(
            "_get_dict_repr must be implemented in serializable subclasses."
        )

    @classmethod
    def _from_dict(cls, dict_repr):
        """Get class from dict representation (excluding the class key).

        Args:
            dict_repr (dict): dictionary representation of class.

        Returns:
            (BaseFilter or None): filter object, if found.
        """
        raise NotImplementedError(
            "from_dict must be implemented in serializable subclasses."
        )


class CompositeFilter(BaseFilter):
    """Filter made of composites of other filters."""
    SUBFILTERS_KEY = "subfilters"
    COMPOSITION_OPERATOR_KEY = "composition_operator"
    AND = "and"
    OR = "or"

    def __init__(self, subfilters_list=None, composition_operator=None):
        """Initialize filter.

        Args:
            subfilters_list (list(BaseFilter) or None): list of subfilters.
            composition_operator (str or None): filter composition operator
                (must be AND or OR). Defaults to AND.
        """
        super(CompositeFilter, self).__init__()
        self._subfilters_list = subfilters_list or []
        self._compositon_operator = composition_operator or self.AND
        if not subfilters_list:
            self._is_valid = False

    def filter_function(self, *args, **kwargs):
        """Filter function.

        Returns:
            (bool): True if item should stay in container, False if it should
                be filtered out.
        """
        if not self._subfilters_list:
            return True
        if self._compositon_operator == self.AND:
            return all([
                subfilter.filter_function(*args, **kwargs)
                for subfilter in self._subfilters_list
            ])
        elif self._compositon_operator == self.OR:
            return any([
                subfilter.filter_function(*args, **kwargs)
                for subfilter in self._subfilters_list
            ])
        else:
            raise FilterError(
                "Unsupported filter compositon operator {0}".format(
                    self._compositon_operator
                )
            )

    @property
    def subfilters(self):
        """Get subfilters composite filter is made of.

        Returns:
            (list(BaseFilter)): list of subfilters.
        """
        return self._subfilters_list

    @property
    def composition_operator(self):
        """Get compositon operator for filter.

        Returns:
            (str): composition operator.
        """
        return self._compositon_operator

    def _to_dict(self):
        """Get dict representation, excluding the class key.

        Returns:
            (dict): dictionary representation.
        """
        return {
            self.SUBFILTERS_KEY: [
                subfilter.to_dict() for subfilter in self._subfilters_list
            ],
            self.COMPOSITION_OPERATOR_KEY: self._compositon_operator,
        }

    @classmethod
    def _from_dict(cls, dict_repr):
        """Get class from dict representation (excluding the class key).

        Args:
            dict_repr (dict): dictionary representation of class.

        Returns:
            (CompositeFilter or None): filter object, if found.
        """
        serialized_subfilters = dict_repr.get(cls.SUBFILTERS_KEY)
        operator = dict_repr.get(cls.COMPOSITION_OPERATOR_KEY)        
        if serialized_subfilters is None or operator is None:
            return None
        subfilters = []
        for subfilter_dict in serialized_subfilters:
            subfilter = filter_from_dict(subfilter_dict)
            if subfilter is not None:
                subfilters.append(subfilter)
        return cls(subfilters, operator)


class CustomFilter(BaseFilter):
    """Filter class built around a given filter function."""
    def __init__(self, function=None):
        """Create filter.

        Args:
            function_ (function or None): if given, override filter function
                with this function.

        Returns:
            (BaseFilter): the created filter class.
        """
        super(CustomFilter, self).__init__()
        if function is None:
            self._is_valid = False
        if function is not None:
            self.filter_function = function


class NoFilter(BaseFilter):
    """Base empty filter class."""
    def __init__(self):
        """Initialize filter."""
        super(NoFilter, self).__init__()
        self._is_valid = False

    def _to_dict(self):
        """Get dict representation, excluding the class key.

        Returns:
            (dict): dictionary representation.
        """
        return {}

    @classmethod
    def _from_dict(cls, dict_repr):
        """Get class from dict representation (excluding the class key).

        Args:
            dict_repr (dict): dictionary representation of class.

        Returns:
            (CompositeFilter or None): filter object, if found.
        """
        return cls()
