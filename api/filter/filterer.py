"""Filterer class to store all filters."""

from collections import OrderedDict
from scheduler.api.serialization.serializable import BaseSerializable
from scheduler.api.enums import OrderedStringEnum

from ._base_filter import BaseFilter, filter_from_dict, FilterError
from .planner_filters import TaskTreeFilter as PlannerTaskTreeFilter
from .schedule_filters import TaskTreeFilter as SchedulerTaskTreeFilter
from .tracker_filters import TaskTreeFilter as TrackerTaskTreeFilter
from .history_filters import TaskTreeFilter as HistoryTaskTreeFilter


class FilterType(OrderedStringEnum):
    """Struct for different types of item to filter."""
    TREE = "tree_filters"
    PLANNER = "planner_filters"
    SCHEDULER = "scheduler_filters"
    TRACKER = "tracker_filters"
    HISTORY = "history_filters"
    GLOBAL = "global_filters"


class GlobalFilter(object):
    """Global filter struct for filters that can be applied to all types."""
    def __init__(
            self,
            tree_filter,
            planner_filter,
            scheduler_filter,
            tracker_filter,
            history_filter):
        """Initialize global filter object.

        Args:
            tree_filter (BaseTreeFilter): version of the filter for tree
                objects.
            planner_filter (BasePlannerFilter): version of the filter for
                planned item objects.
            scheduler_filter (BaseSchedulerFilter): version of the filter
                for scheduled item objects.
            history_filter (BaseTrackerFilter): version of the filter for
                tracked item objects.
            history_filter (BaseHistoryFilter): version of the filter for
                task histories.
        """
        self.tree_filter = tree_filter
        self.planner_filter = planner_filter
        self.scheduler_filter = scheduler_filter
        self.tracker_filter = tracker_filter
        self.history_filter = history_filter

    @classmethod
    def from_tree_filter(cls, tree_filter):
        """Initialize class from tree filter.

        Args:
            tree_filter (BaseTreeFilter): version of the filter for tree
                objects.

        Returns:
            (GlobalFilter): the global filter object for that tree filter.
        """
        return cls(
            tree_filter,
            PlannerTaskTreeFilter(tree_filter),
            SchedulerTaskTreeFilter(tree_filter),
            TrackerTaskTreeFilter(tree_filter),
            HistoryTaskTreeFilter(tree_filter),
        )


class Filterer(BaseSerializable):
    """Filterer class to store all filters"""
    _DICT_TYPE = OrderedDict

    ALL_FILTERS_KEY = "all_filters"
    PINNED_FILTERS_KEY = "pinned_filters"
    PATH_SEPARATOR = "/"

    def __init__(self):
        """Initialize.

        the _all_filters attribute stores all filters in a number of nested
        dicts. These are separated first by type of filter (ie. what type
        of item it is filtering: tree_item, scheduled_item, planned_item,
        tracked_item or history_dict) and then by any number of user defined
        categories and subcategories.
        """
        self._all_filters = {
            FilterType.TREE: OrderedDict(),
            FilterType.PLANNER: OrderedDict(),
            FilterType.SCHEDULER: OrderedDict(),
            FilterType.TRACKER: OrderedDict(),
            FilterType.HISTORY: OrderedDict(),
            FilterType.GLOBAL: OrderedDict(),
        }
        self._pinned_filters = {
            FilterType.TREE: [],
            FilterType.PLANNER: [],
            FilterType.SCHEDULER: [],
            FilterType.TRACKER: [],
            FilterType.HISTORY: [],
            FilterType.GLOBAL: [],
        }

    def _assert_filter_type_is_valid(self, filter_type, allow_tuples=True):
        """Check if filter type is valid and raise error otherwise.

        Args:
            filter_type (FilterType or tuple(FilterType)): filter type.
            allow_tuples (bool): if True, allow tuples of filter_type for the
                first arg.
        """
        if allow_tuples and isinstance(filter_type, tuple):
            filter_types = filter_type
        else:
            filter_types = (filter_type,)
        for filter_type in filter_types:
            if filter_type not in self._all_filters:
                raise FilterError(
                    "Invalid filter type {0}".format(filter_type)
                )

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

    # TODO: make filter type a property of the filter?
    def find_filter_type(self, filter_):
        """Find filter type of given filter.

        Args:
            filter_ (BaseFilter): the filter to check.

        Returns:
            (FilterType or None): the filter type, if found.
        """
        for filter_type, filters_dict in self._all_filters.items():
            if filter_ in filters_dict.values():
                return filter_type
        return None

    def iter_filters(
            self,
            filter_type=None,
            filter_path=None,
            _filter_dict=None):
        """Iterate through all filters.

        Args:
            filter_type (FilterType, tuple(FilterType) or None): if given,
                only iterate through filters of given type(s).
            filter_path (list(str)): if given, only iterate through filters
                saved under the given path. This requires a filter type arg.
            _filter_dict (dict or None): dict of filters to restrict iteration
                to - only used in recursive calls of this function.

        Yields:
            (BaseFilter): the filters saved under the given path.
        """
        # if calling recursively, just loop through every value in the subdicts
        if _filter_dict is not None:
            for filter_or_subdict in _filter_dict.values():
                if isinstance(filter_or_subdict, BaseFilter):
                    yield filter_or_subdict
                else:
                    subdict = filter_or_subdict
                    for filter_ in self.iter_filters(_filter_dict=subdict):
                        yield filter_
            return

        # can't restrict to a filter path without a filter type
        if filter_type is None and filter_path is not None:
            raise FilterError(
                "filter_path arg cannot be used without filter_type arg"
            )

        # get filters_dict to search recursively
        if filter_type is not None:
            self._assert_filter_type_is_valid(filter_type)
            if isinstance(filter_type, tuple):
                filter_types = filter_type
            else:
                filter_types = filter_type
            for filter_type in filter_types:
                filters_dict = self._all_filters.get(filter_type)
                for path_segment in filter_path or []:
                    filters_dict = filters_dict.get(path_segment, {})
        else:
            filters_dict = self._all_filters

        for filter_ in self.iter_filters(_filter_dict=filters_dict):
            yield filter_

    def get_filters_dict(self, filter_type, filter_path=None):
        """Get filters dict for all filters of given type under given path.

        Args:
            filter_type (FilterType): filter type.
            filter_path (list(str) or None): path to filters, if not saved
                directly under the filter_type category. If this path ends with
                the name of a filter, the final element of the list is ignored
                and the returned value is just the dict that filter lives in.

        Returns:
            (dict(str, BaseFilter) or None): filters dict for given type and
                path, if found. This may include nested filters.
        """
        self._assert_filter_type_is_valid(filter_type, allow_tuples=False)
        filter_dict = self._all_filters.get(filter_type)
        prev_filter_dict = None
        for path_segment in filter_path or []:
            prev_filter_dict = filter_dict
            filter_dict = filter_dict.get(path_segment)
            if filter_dict is None:
                return None
        # if final key in path list is for a filter, return prev_dict
        if isinstance(filter_dict, BaseFilter):
            return prev_filter_dict
        return filter_dict

    # def get_filters(self, filter_type, filter_path=None):
    #     """Get all filters of given type under given path.

    #     Args:
    #         filter_type (FilterType): filter type.
    #         filter_path ((list(str) or None): path to filters, if not saved
    #             directly under the filter_type category.

    #     Returns:
    #         (dict(str, BaseFilter) or None): filters dict for given type and
    #             path, if found. This may include nested filters.
    #     """
    #     self._assert_filter_type_is_valid(filter_type)
    #     filter_dict = self._all_filters.get(filter_type)
    #     for path_segment in filter_path or []:
    #         filter_dict = filter_dict.get(path_segment)
    #         if filter_dict is None:
    #             return None
    #     return filter_dict

    def get_pinned_filters(self, filter_type):
        """Get all pinned filters of given type.

        Args:
            filter_type (FilterType): filter type.

        Returns:
            (list(BaseFilter)): pinned filters list.
        """
        self._assert_filter_type_is_valid(filter_type)
        return self._pinned_filters.get(filter_type)

    def get_global_pinned_filters(self):
        """Get global pinned filters.

        Returns:
            (list(BaseFilter)): pinned filters list.
        """
        return self._pinned_filters[FilterType.GLOBAL]

    def get_filter(self, filter_type, filter_path):
        """Get filter with given type at given path.

        Args:
            filter_type (FilterType): filter type.
            filter_path (list(str)): path to filter, including name.

        Returns:
            (BaseFilter or None): filter at given path, if exists.
        """
        filter_dict = self._all_filters.get(filter_type)
        for path_segment in filter_path:
            if not filter_dict:
                break
            filter_dict = filter_dict.get(path_segment)
        if isinstance(filter_dict, BaseFilter):
            return filter_dict
        return None

    # instead of a get anyway
    # def get_all_filters(self):
    #     """Get all filters.

    #     Returns:
    #         (list(BaseFilter)): list of all filters.
    #     """
    #     return [
    #         filter_
    #         for subdict in self._all_filters.values()
    #         for filter_ in subdict.values()
    #     ]

    # def clear_filter_caches(self, filter_type=None, filter_name=None):
    #     """Clear filter caches for all filters.

    #     Args:
    #         filter_type (FilterType or None): if given, only clear filters
    #             with given type.
    #         filter_name (str or None): if given, only clear filters with
    #             given name.
    #     """
    #     for filter_type_, filters_dict in self._all_filters.items():
    #         if filter_type_ is not None and filter_type_ != filter_type:
    #             continue
    #         if filter_name is not None:
    #             filter_ = filters_dict.get(filter_name)
    #             if filter_ is not None:
    #                 filter_.clear_cache()
    #             continue
    #         for filter_ in filters_dict.values():
    #             filter_.clear_cache()

    def clear_filter_caches(self, filter_type=None, filter_path=None):
        """Clear filter caches for all filters.

        Args:
            filter_type (FilterType, tuple(FilterType) or None): if given,
                only clear filters of given type(s).
            filter_path (list(str)): if given, only clear filters saved under
                the given path. This requires a filter type arg.
        """
        for filter_ in self.iter_filters(filter_type, filter_path):
            filter_.clear_cache()

    @classmethod
    def _deserialize_filters_dict(cls, filters_dict):
        """Recursive method to deserialize nested filters in a filters dict.

        Args:
            filters_dict (dict): nested dictionary of serialized filters.

        Returns:
            (dict): nested dictionary of deserialized filters.
        """
        deserialized_dict = OrderedDict()
        for key, subdict in filters_dict.items():
            # TODO: require in ui that _FILTER_CLASS_NAME_KEY not the name
            # of any filter paths
            if BaseFilter._FILTER_CLASS_NAME_KEY in subdict:
                filter_ = filter_from_dict(subdict)
                if filter_:
                    deserialized_dict[key] = filter_
            else:
                deserialized_subdict = cls._deserialize_filters_dict(subdict)
                if deserialized_subdict:
                    deserialized_dict[key] = deserialized_subdict
        return deserialized_dict

    @classmethod
    def from_dict(cls, dictionary):
        """Initialise class from dictionary.

        Args:
            dictionary (dict): the dictionary we're deserializing from.
        """
        filterer = cls()
        all_filters = dictionary.get(cls.ALL_FILTERS_KEY, {})
        for filter_type, filters_dict in all_filters.items():
            if filter_type in filterer._all_filters:
                filterer._all_filters[filter_type] = (
                    cls._deserialize_filters_dict(filters_dict)
                )

        pinned_filters = dictionary.get(cls.PINNED_FILTERS_KEY, {})
        for filter_type, pin_list in pinned_filters.items():
            filter_type = FilterType.from_string(filter_type)
            if filter_type is None:
                continue
            filterer_pin_list = filterer._pinned_filters[filter_type]
            for filter_path_string in pin_list:
                filter_path = filter_path_string.split(cls.PATH_SEPARATOR)
                filter_ = filterer.get_filter(filter_path)
                if filter_ is not None:
                    filterer._pinned_filters[filter_type].append(filter_)

        return filterer

    def _serialize_filters_dict(
            self,
            filters_dict,
            filter_type,
            filter_path,
            pins_list,
            global_pins_list):
        """Recursive method to serialize nested filters in a filters dict.

        Args:
            filters_dict (dict): nested dictionary of filters.
            filter_type (FilterType): filter type of dict currently being
                serialized.
            filter_path (list): list of path so far.
            pins_list (list): list of pinned filters for given type. This list
                consists of BaseFilters, which this serialization process
                should swap out for paths.
            global_pins_list (list): list of global pinned filters. This list
                consists of BaseFilters, which this serialization process
                should swap out for paths.

        Returns:
            (dict): nested dictionary of serialized filters.
        """
        serialized_dict = OrderedDict()
        for key, filter_or_subdict in filters_dict.items():
            if isinstance(filter_or_subdict, BaseFilter):
                filter_ = filter_or_subdict
                serialized_subdict = filter_.to_dict()
                # add to pin list if needed
                for list_ in list(set([pins_list, global_pins_list])):
                    if filter_ in list_:
                        index = list_.index(filter_)
                        list_[index] = self.PATH_SEPARATOR.join(
                            filter_path + [key]
                        )
            else:
                serialized_subdict = self._serialize_filters_dict(
                    filter_or_subdict,
                    filter_type,
                    filter_path + [key],
                    pins_list,
                    global_pins_list,
                )
            if serialized_subdict:
                serialized_dict[key] = serialized_subdict
        return serialized_dict

    def to_dict(self):
        """Serialize class as dictionary.

        Returns:
            (dict): the serialized dictionary.
        """
        dict_repr = {}
        all_filters_dict = {}
        pinned_filters_dict = {}
        for filter_type, pin_list in self._pinned_filters.items():
            pinned_filters_dict[filter_type] = pin_list[:]
        global_pins_list = pinned_filters_dict[FilterType.GLOBAL]

        for filter_type, filters_dict in self._all_filters.items():
            serialized_dict = self._serialize_filters_dict(
                filters_dict,
                filter_type=filter_type,
                filter_path=[],
                pins_list=pinned_filters_dict[filter_type],
                global_pins_list=global_pins_list,
            )
            if serialized_dict:
                all_filters_dict[filter_type] = serialized_dict
        if all_filters_dict:
            dict_repr[self.ALL_FILTERS_KEY] = all_filters_dict

        for filter_type, pin_list in pinned_filters_dict.items():
            pinned_filters_dict[filter_type] = [
                f for f in pin_list if not isinstance(f, BaseFilter)
            ]
        dict_repr[self.PINNED_FILTERS_KEY] = pinned_filters_dict

        return dict_repr
