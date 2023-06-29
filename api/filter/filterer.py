"""Filterer class to store all filters."""

from collections import OrderedDict
from scheduler.api.serialization.serializable import BaseSerializable
from scheduler.api.enums import OrderedStringEnum

from ._base_filter import filter_from_dict, FilterError


class FilterType(OrderedStringEnum):
    """Struct for different types of item to filter."""
    TREE = "tree_filters"
    PLANNER = "planner_filters"
    SCHEDULER = "scheduler_filters"
    HISTORY = "history_filters"


# TODO: I think filters at least should be editable
class Filterer(BaseSerializable):
    """Filterer class to store all filters"""
    _DICT_TYPE = OrderedDict

    def __init__(self):
        """Initialize."""
        self._all_filters = {
            FilterType.TREE: OrderedDict(),
            FilterType.PLANNER: OrderedDict(),
            FilterType.HISTORY: OrderedDict(),
            FilterType.SCHEDULER: OrderedDict(),
        }

    def _assert_filter_type_is_valid(self, filter_type):
        """Check if filter type is valid and raise error otherwise.

        Args:
            filter_type (FilterType): filter type.
        """
        if filter_type not in self._all_filters:
            raise FilterError("Invalid filter type {0}".format(filter_type))

    # def check_filter_name_available(self, name):
    #     """Check if given filter name is available.

    #     Args:
    #         name (str or None): filter name to check.

    #     Returns:
    #         (bool): True if name has not been used, otherwise false.
    #     """
    #     return name is not None and all([
    #         name not in subdict for subdict in self._all_filters.values()
    #     ])

    def get_filters(self, filter_type):
        """Get all filters of given type.
        
        Args:
            filter_type (FilterType): filter type.

        Returns:
            (dict(str, BaseFilter) or None): filters dict for given type, if
                found.
        """
        self._assert_filter_type_is_valid(filter_type)
        return self._all_filters.get(filter_type)

    def get_all_filters(self):
        """Get all filters.

        Returns:
            (list(BaseFilter) or None): list of all filters if found.
        """
        return [
            filter_
            for subdict in self._all_filters.values()
            for filter_ in subdict.values()
        ]

    # def add_filter(self, filter_type, filter_):
    #     """Add given filter.

    #     Args:
    #         filter_type (FilterType): filter type.
    #         field_filter (BaseFilter): the field filter to add.
    #     """
    #     self._assert_filter_type_is_valid(filter_type)
    #     if self.check_filter_name_available(filter_.name):
    #         self._all_filters[filter_type][filter_.name] = filter_

    # def modify_filter(self, filter_type, old_name, filter_):
    #     """Modify given filter.

    #     Args:
    #         filter_type (FilterType): filter type.
    #         old_name (str): old name of filter we're modifying.
    #         filter_ (BaseFilter): the filter after modification.
    #     """
    #     self._assert_filter_type_is_valid(filter_type)
    #     filters = self._all_filters[filter_type]
    #     if old_name not in filters:
    #         return
    #     if old_name == filter_.name:
    #         filters[old_name] = filter_
    #     else:
    #         if self.check_filter_name_available(filter_.name):
    #             for _ in range(len(filters)):
    #                 k, v = filters.popitem(last=False)
    #                 if k == old_name:
    #                     filters[filter_.name] = filter_
    #                 else:
    #                     filters[k] = v

    # def remove_filter(self, filter_type, name):
    #     """Remove filter with given name.

    #     Args:
    #         filter_type (FilterType): filter type.
    #         name (str): name of filter to remove.
    #     """
    #     self._assert_filter_type_is_valid(filter_type)
    #     filters = self._all_filters[filter_type]
    #     if name in filters:
    #         del filters[name]

    def clear_filter_caches(self):
        """Clear filter caches for all filters."""
        for filter_ in self.get_all_filters():
            filter_.clear_cache()

    @classmethod
    def from_dict(cls, dictionary):
        """Initialise class from dictionary.

        Args:
            dictionary (dict): the dictionary we're deserializing from.
        """
        filterer = cls()
        for filter_type, filters_dict in dictionary.items():
            if filter_type in filterer._all_filters:
                for name, filter_dict in filters_dict.items():
                    filter_ = filter_from_dict(filter_dict)
                    if filter_:
                        filterer._all_filters[filter_type][name] = filter_
        return filterer

    def to_dict(self):
        """Serialize class as dictionary.

        Returns:
            (dict): the serialized dictionary.
        """
        dict_repr = {}
        for filter_type, filters_dict in self._all_filters.items():
            if filters_dict:
                dict_repr[filter_type] = {
                    name: filter_.to_dict()
                    for name, filter_ in filters_dict.items()
                }
        return dict_repr
