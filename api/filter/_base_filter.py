"""Base filter class."""

from collections import Hashable

from scheduler.api.enums import OrderedStringEnum
from scheduler.api.utils import fallback_value


class FilterType(OrderedStringEnum):
    """Struct for different types of item to filter.
    
    This defines the type of component that a filter is used on (eg. tree
    item, planned item, scheduled item etc.). If a filter is not used on
    any of these scheduler project components, it will just have 'general'
    type. If it can be used on all these components, it has 'global' type.
    """
    TREE = "tasks"
    PLANNER = "planner"
    SCHEDULER = "scheduler"
    TRACKER = "tracker"
    HISTORY = "history"
    GLOBAL = "global"
    GENERAL = "general"

    @classmethod
    def scheduler_filter_types(cls):
        """Return all filter types of scheduler components.

        Returns:
            (list): list of filter types that correspond to components
                in the scheduler. Specifically, this doesn't include the
                Global and General filter types.
        """
        return [
            cls.TREE,
            cls.PLANNER,
            cls.SCHEDULER,
            cls.TRACKER,
            cls.HISTORY,
        ]


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
    filter_class_name = dict_repr.get(BaseFilter._FILTER_CLASS_NAME_KEY)
    filter_class = _SERIALIZABLE_FILTER_CLASSES.get(filter_class_name)
    if filter_class is not None:
        filter_ = filter_class._from_dict(dict_repr)
        filter_.set_name(dict_repr.get(BaseFilter._NAME_KEY))
        return filter_
    return None


class BaseFilter(object):
    """Base filter class, with function for filtering items in a container."""
    _NAME_KEY = "name"
    _FILTER_CLASS_NAME_KEY = "filter_class"
    _FILTER_CLASS_NAME = None

    def __init__(self):
        """Initialize.

        Attributes:
            _filter_type (FilterType or None): filter type
            _composite_filter_class (class or None): the class used to build
                composite filters with and/or operators.
            _is_valid (bool): whether or not filter is valid.
            _name (str): name of filter.
            _filter_cache (dict(tuple, bool)): dictionary of items that have
                already been run through this filter and the resulting value,
                used to save recalculating.
        """
        self._filter_type = FilterType.GENERAL
        self._composite_filter_class = CompositeFilter
        # ^ TODO: make these class attributes? Might just need to be careful
        # with the multi-class-inheritance
        self._is_valid = True
        self._name = None
        # set filter cache to None in classes we don't want to cache
        # filter caches should be cleared after every edit
        self._filter_cache = {}

    @property
    def name(self):
        """Get name of filter, if exists.

        Returns:
            (str or None): filter name.
        """
        return self._name

    @property
    def filter_type(self):
        """Get type of filter.

        Returns:
            (FilterType): filter type.
        """
        return self._filter_type

    def set_name(self, name):
        """Set name of filter.

        Args:
            name (str): filter name.
        """
        self._name = name

    def clear_cache(self):
        """Clear filter cache."""
        if self._filter_cache is not None:
            self._filter_cache = {}

    def filter_function(self, *args, **kwargs):
        """Filter function.

        Similarly to the distinction between run and _run in edit classes,
        _filter_function determines the class-specific implementation, and is
        called by filter_function, which defines generic behaviour for all
        filter functions.

        Returns:
            (bool): True if item should stay in container, False if it should
                be filtered out.
        """
        if not self._is_valid:
            return True
        if self._filter_cache is not None:
            # TODO: remove the **kwargs in filter_func, they're not supported
            # TODO: will this always be enough? may need to redo _get_cache_key
            # but just default to this value
            hashable_args = [
                arg for arg in (list(args) + list(kwargs.values()))
                if isinstance(arg, Hashable)
            ]
            cache_key = tuple(hashable_args)
            if cache_key in self._filter_cache:
                return self._filter_cache[cache_key]
            value = self._filter_function(*args, **kwargs)
            self._filter_cache[cache_key] = value
            return value
        return self._filter_function(*args, **kwargs)

    def _filter_function(self, *args, **kwargs):
        """Filter function implementation.

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
                subfilters_list.extend(f._subfilters_list)
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
                subfilters_list.extend(f._subfilters_list)
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
            dict_repr = self._to_dict()
            dict_repr[self._FILTER_CLASS_NAME_KEY] = self._FILTER_CLASS_NAME
            if self.name is not None:
                dict_repr[self._NAME_KEY] = self.name
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
    AND = "AND"
    OR = "OR"

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

    def _filter_function(self, *args, **kwargs):
        """Filter function.

        Returns:
            (bool): True if item should stay in container, False if it should
                be filtered out.
        """
        if not self._subfilters_list:
            return True
        if self._compositon_operator == self.AND:
            return all([
                subfilter._filter_function(*args, **kwargs)
                for subfilter in self._subfilters_list
            ])
        elif self._compositon_operator == self.OR:
            return any([
                subfilter._filter_function(*args, **kwargs)
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
            self._filter_function = function
        self._filter_cache = None


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
