"""Converter module for conversion between filters of different types."""

from ._base_filter import CompositeFilter, FilterError, FilterType, NoFilter

from .tree_filters import CompositeTreeFilter, NoFilter as TreeNoFilter
from .planner_filters import (
    CompositePlannerFilter,
    TaskTreeFilter as PlannerTaskTreeFilter,
    NoFilter as PlannerNoFilter,
)
from .schedule_filters import (
    CompositeSchedulerFilter,
    TaskTreeFilter as SchedulerTaskTreeFilter,
    NoFilter as SchedulerNoFilter,
)
from .tracker_filters import (
    CompositeTrackerFilter,
    TaskTreeFilter as TrackerTaskTreeFilter,
    NoFilter as TrackerNoFilter,
)
from .history_filters import (
    CompositeHistoryFilter,
    TaskTreeFilter as HistoryTaskTreeFilter,
    NoFilter as HistoryNoFilter,
)


COMPOSITE_CLASSES = {
    FilterType.TREE: CompositeTreeFilter,
    FilterType.PLANNER: CompositePlannerFilter,
    FilterType.SCHEDULER: CompositeSchedulerFilter,
    FilterType.TRACKER: CompositeTrackerFilter,
    FilterType.HISTORY: CompositeHistoryFilter,
}
EMPTY_FILTER_CLASSES = {
    FilterType.TREE: TreeNoFilter,
    FilterType.PLANNER: PlannerNoFilter,
    FilterType.SCHEDULER: SchedulerNoFilter,
    FilterType.TRACKER: TrackerNoFilter,
    FilterType.HISTORY: HistoryNoFilter,
}
TASK_TREE_CLASSES = {
    FilterType.PLANNER: PlannerTaskTreeFilter,
    FilterType.SCHEDULER: SchedulerTaskTreeFilter,
    FilterType.TRACKER: TrackerTaskTreeFilter,
    FilterType.HISTORY: HistoryTaskTreeFilter,
}
TASK_TREE_CLASSES_TUPLE = tuple(TASK_TREE_CLASSES.values())


class FilterConverter(object):
    """Filter converter class for converting filters."""
    def __init__(self):
        """Initialize class."""
        pass

    def can_convert(self, filter_, filter_type):
        """Check if given filter can be converted to new type.

        Args:
            filter_ (BaseFilter): filter to check.
            filter_type (FilterType): type to convert to.

        Returns:
            (bool): whether or not filter can be converted to given type.
        """
        return self.convert(filter_, filter_type, _test_run=True)

    def convert(self, filter_, filter_type, raise_error=True, _test_run=False):
        """Convert filter to new type.

        Args:
            filter_ (BaseFilter): filter to convert.
            filter_type (FilterType): type to convert to.
            raise_error (bool): if True, raise error when filter cannot be
                converted.
            _test_run (bool): if True, just run this to check if the conversion
                is possible, rather than actually doing the conversion. This
                is just here for convenience so we don't need to repeat the
                logic of this method in the can_convert method.

        Raises:
            (FilterError): if filter cannot be converted and raise_error=True.

        Returns:
            (BaseFilter or None): converted filter, if filter can be converted.
        """
        # case 1: all filters can have general type, no conversion needed
        if filter_type == FilterType.GENERAL:
            return _test_run or filter_

        # case 2: filter_type unchanged, no conversion needed
        if filter_type == filter_.filter_type:
            return _test_run or filter_

        # case 3: all empty filter classes can be converted trivially
        if isinstance(filter_, NoFilter):
            return (
                _test_run or EMPTY_FILTER_CLASSES.get(filter_type, NoFilter)()
            )

        # case 3: convert from a tree filter to any scheduler component type 
        if (filter_.filter_type == FilterType.TREE
                and filter_type in TASK_TREE_CLASSES):
            return _test_run or TASK_TREE_CLASSES.get(filter_type)(filter_)

        # case 4: convert back to a tree filter from a task_tree_filter class
        if (filter_type == FilterType.TREE and
                isinstance(filter_, TASK_TREE_CLASSES_TUPLE)):
            return _test_run or filter_._tree_filter

        # case 5: composite filters - convert all subfilters
        if isinstance(filter_, CompositeFilter):
            converted_subfilters = []
            for subfilter in filter_.subfilters:
                converted_subfilter = self.convert(
                    subfilter,
                    filter_type,
                    raise_error=raise_error,
                    _test_run=_test_run,
                )
                # if any subfilter can't be converted, the composite can't be
                if _test_run:
                    if not converted_subfilter:
                        return False
                    continue
                if converted_subfilter is None:
                    return None
                converted_subfilters.append(converted_subfilter)
            if _test_run:
                return True
            return COMPOSITE_CLASSES.get(filter_type, CompositeFilter)(
                converted_subfilters,
                filter_.composition_operator,
            )

        # otherwise we cannot convert
        if _test_run:
            return False
        if raise_error:
            raise FilterError(
                "Filter {0} cannot be converted to filter type {1}".format(
                    filter_.name,
                    filter_type,
                )
            )
        return None

    def quasiconvert(self, filter_, filter_type):
        """Convert filter, or largest selection of subfilters to new type.

        This returns a converted filter, if the filter can be converted. If
        the filter cannot be converted and the filter is an 'AND' composite,
        this method instead converts any convertible subfilters of the filter
        and returns a composite of those. Thus the returned filter is
        guaranteed to be either as restrictive as, or less restrictive than,
        the original filter.

        This is primarily intended to allow eg. filters on planned items that
        have some subfilter which filters only tree items, to be used to
        partially restrict the outliner tree view, even if some of the fields
        of the full filter do not apply to tree items.

        Args:
            filter_ (BaseFilter): filter to quasiconvert.
            filter_type (FilterType): type to convert to.

        Returns:
            (BaseFilter): the quasiconverted filter.
        """
        full_conversion = self.convert(filter_, filter_type, raise_error=False)
        if full_conversion is not None:
            return full_conversion

        if (not isinstance(filter_, CompositeFilter)
                or filter_.composition_operator == filter_.OR):
            # note: 'OR' composites cannot be quasiconverted, as these don't
            # guarantee a less restrictive filter will be returned
            return EMPTY_FILTER_CLASSES.get(filter_type, NoFilter)()

        converted_subfilters = []
        for subfilter in filter_.subfilters:
            converted_subfilter = self.quasiconvert(subfilter, filter_type)
            if converted_subfilter:
                # only add subfilters that aren't NoFilter
                converted_subfilters.append(converted_subfilter)
        return COMPOSITE_CLASSES.get(filter_type, CompositeFilter)(
            converted_subfilters,
            filter_.AND,
        )


FILTER_CONVERTER = FilterConverter()


def can_convert_filter(filter_, filter_type):
    """Check if given filter can be converted to new type.

    Args:
        filter_ (BaseFilter): filter to check.
        filter_type (FilterType): type to convert to.

    Returns:
        (bool): whether or not filter can be converted to given type.
    """
    return FILTER_CONVERTER.can_convert(filter_, filter_type)


def convert_filter(filter_, filter_type, raise_error=True):
        """Convert filter to new type.

        Args:
            filter_ (BaseFilter): filter to convert.
            filter_type (FilterType): type to convert to.
            raise_error (bool): if True, raise error when filter cannot be
                converted.

        Raises:
            (FilterError): if filter cannot be converted and raise_error=True.

        Returns:
            (BaseFilter or None): converted filter, if filter can be converted.
        """
        return FILTER_CONVERTER.convert(
            filter_,
            filter_type,
            raise_error=raise_error,
        )


def quasiconvert_filter(filter_, filter_type):
    """Convert filter, or largest selection of subfilters to new type.

    See notes in FilterConverter class for explanation of how this works.

    Args:
        filter_ (BaseFilter): filter to quasiconvert.
        filter_type (FilterType): type to convert to.

    Returns:
        (BaseFilter): the quasiconverted filter.
    """
    return FILTER_CONVERTER.quasiconvert(filter_, filter_type)
