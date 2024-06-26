"""Filter manager for managing filtering for each model.

Each tab is intended to have its own filter manager class. This allows
us to maintain ui-specific properties for each tree item without
editing the underlying tree item data, eg. whether or not the item
is being filtered for in the current tab.
"""

from scheduler.api.edit.filter_edit import (
    AddFilterEdit,
    RemoveFilterEdit,
    ModifyFilterEdit,
)
# from scheduler.api.filter import FilterType
from scheduler.api.filter import FilterType
from scheduler.api.filter.conversion import convert_filter, quasiconvert_filter
from scheduler.api.filter.tree_filters import NoFilter, FilterByItem
from scheduler.api.tree.base_task_item import BaseTaskItem
from scheduler.api.utils import fallback_value

from ._base_manager import require_class, BaseManager, ManagerError


class FilterManager(BaseManager):
    """Filter manager to filter items and apply filter edits.

    This stores attributes for each tree item in internal data dicts, keyed by
    the tree item.

    Attributes:
        IS_SELECTED_FOR_FILTERING (bool): whether or not the user has selected
            to filter the current item out of the tree.
        IS_FILTERED_OUT (bool): whether or not the item should be filtered out
            of the tree (either because the user selected to filter it out, or
            because one of its ancestors has been selected to be filtered out).
        IS_EXPANDED (bool): whether or not the given item is expanded in the
            outliner.
    """
    IS_SELECTED_FOR_FILTERING = "is_selected_for_filtering"
    IS_FILTERED_OUT = "is_filtered_out"
    IS_EXPANDED = "is_expanded"

    ATTRIBUTE_DEFAULTS = {
        IS_SELECTED_FOR_FILTERING: False,
        IS_FILTERED_OUT: False,
        IS_EXPANDED: True,
    }
    USER_PREFS_ATTRIBUTES = [
        IS_SELECTED_FOR_FILTERING,
        IS_EXPANDED,
    ]
    FILTERED_TASKS_PREF = "task_filters"
    FIELD_FILTERS_PREF = "field_filters"
    ACTIVE_FIELD_FILTER_PREF = "active_field_filter"

    def __init__(self, user_prefs, tree_root, filterer, filter_type):
        """Initialise class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            tree_root (TaskRoot): root task object.
            filterer (Filterer): filterer class for storing filters.
            filter_type (FilterType): the filter type that this filter manager
                manages. This corresponds to the tab that it's used on, and
                so primarily defines the type of component this manager is
                filtering. However note that these filters may still be used
                on other types of component (eg. the field filters will be
                partially applied to the tree outliner, and hybrid views in
                the scheduler and planner tabs may require the filters to be
                converted to be applied to other component types).

        Attributes:
            _tree_data (dict(str, dict)): additional tree data for each tree
                item.
            _filtered_tree_items (set(str)): set of items we're filtering out.
            _active_field_filter (FieldFilter or CompositeFilter): the
                currently selected field filter.
            _current_tree_item (BaseTaskItem): the currently selected task
                item.
        """
        self._filterer = filterer
        self._tree_root = tree_root
        self._archive_tree_root = tree_root.archive_root
        super(FilterManager, self).__init__(
            user_prefs,
            filter_type=filter_type,
            name=filter_type,
            suffix="filter_manager",
        )

        self._tree_data = {}
        self._filtered_tree_items = set()
        self._current_tree_item = None
        self._active_field_filter = None
        self._tree_item_filter = None
        self._combined_filter = None
        self._setup_from_user_prefs()

    def _setup_from_user_prefs(self):
        """Setup filtering based on user prefs."""
        # tree item attributes
        filter_attrs = self._project_user_prefs.get_attribute(
            [self._name, self.FILTERED_TASKS_PREF],
            {}
        )
        for tree_item, attr_dict in filter_attrs.items():
            if tree_item and attr_dict:
                for attr, value in attr_dict.items():
                    self._tree_data.setdefault(tree_item, {})[attr] = value
                    if attr == self.IS_SELECTED_FOR_FILTERING and value==True:
                        self._filtered_tree_items.add(tree_item)

        # active field filter
        active_filter_name = self._project_user_prefs.get_attribute(
            [self._name, self.ACTIVE_FIELD_FILTER_PREF]
        )
        if active_filter_name is not None:
            self._active_field_filter = self.get_field_filter(
                [active_filter_name]
            )

    def clear_filter_caches(self):
        """Clear all filter caches."""
        self._filterer.clear_filter_caches()
        # TODO: filterer only stores field filters I think?
        # so I need to also take the active filters and clear them
        # or maybe add the active filters to the filterer as well, in
        # an unsaved filters section?
        # QUESTION: should this only clear filter caches for filters
        # owned by this manager? If so, need to pass the filter type
        # to clear filter_caches arg too

    def assert_filter_type(self, filter_type):
        """Assert that filter type of manager is correct one.

        Args:
            filter_type (FilterType): type to check.

        Raises:
            (ManagerError): if filter type doesn't match manager filter type.
        """
        if filter_type != self._filter_type:
            raise ManagerError(
                "FilterManager has incorrect type {0}, not {1}".format(
                    self._filter_type,
                    filter_type,
                )
            )

    ### Tree item filtering ###
    def has_attribute(self, tree_item, attribute):
        """Check if tree item already has attribute defined in internal dict.

        Args:
            tree_item (BaseTaskItem): tree item to query for.
            atttribute (str): attribute name.

        Returns:
            (bool): whether or not given attribute is currently defined in
                internal dict.
        """
        return attribute in self._tree_data.setdefault(tree_item, {})

    def get_attribute(self, tree_item, attribute, default=None):
        """Get the attribute for the given tree item.

        Args:
            tree_item (BaseTaskItem): tree item to query for.
            atttribute (str): attribute name.
            default (variant or None): default value for attribute.
                If None, try to find from ATTRIBUTE_DEFAULTS instead.

        Returns:
            (variant): value of attribute for given item.
        """
        item_dict = self._tree_data.setdefault(tree_item, {})
        default = fallback_value(
            default,
            self.ATTRIBUTE_DEFAULTS.get(attribute, None),
        )
        return item_dict.setdefault(attribute, default)

    def set_attribute(self, tree_item, attribute, value, default=None):
        """Set the attribute for the given tree item.

        Args:
            tree_item (BaseTaskItem): tree item to set attribute for.
            atttribute (str): attribute name.
            value (variant): value to set.
            default (variant or None): default value for attribute.
                If None, try to find from ATTRIBUTE_DEFAULTS instead.
        """
        if attribute in self.USER_PREFS_ATTRIBUTES:
            default = fallback_value(
                default,
                self.ATTRIBUTE_DEFAULTS.get(attribute, None),
            )
            self._project_user_prefs.set_attribute(
                [self._name, self.FILTERED_TASKS_PREF, tree_item, attribute],
                value,
                default,
            )
        item_dict = self._tree_data.setdefault(tree_item, {})
        item_dict[attribute] = value

    def is_filtered_out(self, tree_item):
        """Check if the given tree item is filtered out.

        Args:
            tree_item (BaseTaskItem): tree item to query.

        Returns:
            (bool): whether or not the given item is being filtered out.
        """
        tree_field_filter = quasiconvert_filter(
            self.field_filter,
            FilterType.TREE,
        )
        if (tree_item.parent is not None and tree_item not in
                tree_item.parent.get_filtered_children(tree_field_filter)):
            return True

        if self.has_attribute(tree_item, self.IS_FILTERED_OUT):
            return self.get_attribute(tree_item, self.IS_FILTERED_OUT)

        if self.is_selected_for_filtering(tree_item):
            return_val = True
        elif tree_item.parent is not None:
            return_val = self.is_filtered_out(tree_item.parent)
        else:
            return_val = False
        self.set_attribute(tree_item, self.IS_FILTERED_OUT, return_val)
        return return_val

    def is_selected_for_filtering(self, tree_item):
        """Check if the given tree item has been selected for filtering.

        If this is True, its checkbox should be deselected in the ui.

        Args:
            tree_item (BaseTaskItem): tree item to query.

        Returns:
            (bool): whether or not the given item is selected for filtering.
        """
        return self.get_attribute(tree_item, self.IS_SELECTED_FOR_FILTERING)

    def siblings_are_selected_for_filtering(self, tree_item):
        """Check if all this tree_item's siblings are selected for filtering.

        Args:
            tree_item (BaseTaskItem): tree item to query.

        Returns:
            (bool): whether or not the item's siblings are all selected for
                filtering.
        """
        return all([
            self.is_selected_for_filtering(sibling)
            for sibling in tree_item.get_all_siblings()
        ])

    def ancestor_sibs_selected_for_filter(self, tree_item):
        """Check if all item's ancestoral siblings are selected for filtering.

        Args:
            tree_item (BaseTaskItem): tree item to query.

        Returns:
            (bool): whether or not the item's ancestoral siblings (ie. siblings
                of tree_item or one of it's ancestors) are all selected for
                filtering.
        """
        while tree_item.parent:
            if not self.siblings_are_selected_for_filtering(tree_item):
                break
            tree_item = tree_item.parent
        else:
            return True
        return False

    def is_expanded(self, tree_item, default=None):
        """Check if the given tree item has been expanded in the outliner.

        Args:
            tree_item (BaseTaskItem): tree item to query.
            default (bool or None): default value to use, if given.

        Returns:
            (bool): whether or not the given item is expanded.
        """
        default = fallback_value(
            default,
            self.is_task_category(tree_item)
        )
        return self.get_attribute(tree_item, self.IS_EXPANDED, default=default)

    # TODO: update names of these functions to filter_tree_item etc.?
    def filter_item(self, tree_item, from_user_selection=True):
        """Add tree item to filter list.

        Args:
            tree_item (BaseTaskItem): tree item to filter out.
            from_user_selection (bool): if True, this is being set because the
                user has selected to filter out the given item. Otherwise,
                this is being called recursively because one of this item's
                ancestors has been selected for filtering.
        """
        if from_user_selection:
            self.set_attribute(tree_item, self.IS_SELECTED_FOR_FILTERING, True)
        self.set_attribute(tree_item, self.IS_FILTERED_OUT, True)
        self._filtered_tree_items.add(tree_item)
        self._tree_item_filter = None
        self._combined_filter = None
        for child in tree_item.get_all_children():
            self.filter_item(child, from_user_selection=False)

    def unfilter_item(self, tree_item, from_user_selection=True):
        """Remove tree item from filter list.

        Args:
            tree_item (BaseTaskItem): tree item to remove filter from.
            from_user_selection (bool): if True, this is being set because the
                user has selected to unfilter the given item. Otherwise, this
                is being called recursively because one of this item's
                ancestors has been deselected for filtering.
        """
        if from_user_selection:
            self.set_attribute(tree_item, self.IS_SELECTED_FOR_FILTERING, False)
            parent_item = tree_item.parent
            # if parent item is filtered, we can't unfilter, so return
            if parent_item and self.is_filtered_out(parent_item):
                return

        # if given item is selected for filtering, we can't unfilter, so return
        if self.is_selected_for_filtering(tree_item):
            return

        self.set_attribute(tree_item, self.IS_FILTERED_OUT, False)
        self._filtered_tree_items.discard(tree_item)
        self._tree_item_filter = None
        self._combined_filter = None
        for child in tree_item.get_all_children():
            self.unfilter_item(child, from_user_selection=False)

    def filter_ancestoral_siblings(self, tree_item):
        """Add all siblings of tree item and ancestors to filter list.

        Args:
            tree_item (BaseTaskItem): tree item to filter out.
        """
        for sibling in tree_item.get_all_siblings():
            self.filter_item(sibling)
        if tree_item.parent:
            self.filter_ancestoral_siblings(tree_item.parent)

    def unfilter_ancestoral_siblings(self, tree_item):
        """Remove all sibling of tree item and ancestors from filter list.

        Args:
            tree_item (BaseTaskItem): tree item to unfilter.
        """
        for sibling in tree_item.get_all_siblings():
            self.unfilter_item(sibling)
        if tree_item.parent:
            self.unfilter_ancestoral_siblings(tree_item.parent)

    def expand_item(self, tree_item, value, default=None):
        """Mark tree item as collapsed/expanded in the outliner.

        Args:
            tree_item (BaseTaskItem): tree item to expand or collapse.
            value (bool): the value to mark it as (True means expanded, False
                means collapsed).
            default (bool or None): default value to use, if given.
        """
        default = fallback_value(
            default,
            self.is_task_category(tree_item),
        )
        self.set_attribute(tree_item, self.IS_EXPANDED, value, default=default)

    def set_expanded_from_filtered(self, tree_item=None):
        """Set filtered tree items as collapsed and unfiltered as expanded.

        This only expands TaskCategory items, to avoid opening full tree
        unnecessarily.

        Args:
            item (BaseTaskItem or None): tree item to set from. If not given,
                use root.

        Returns:
            (bool): whether or not action was successful.
        """
        if tree_item is None:
            tree_item = self._tree_root
        if self.is_filtered_out(tree_item):
            self.expand_item(tree_item, False)
        else:
            if self.is_task_category(tree_item):
                self.expand_item(tree_item, True)
            for child in tree_item.get_all_children():
                self.set_expanded_from_filtered(child)
        return True
    

    # @require_class(BaseTaskItem, raise_error=True)
    # def get_filtered_children(self, tree_item):
    #     """Get filtered children of tree item.

    #     Args:
    #         tree_item (BaseTaskItem): item to get chidren of.

    #     Returns:
    #         (list(BaseTaskItem)): children with filter applied.
    #     """
    #     with tree_item.filter_children(self.tree_filter):
    #         return tree_item.get_all_children()

    def set_current_tree_item(self, item):
        """Set given tree item as the currently selected one.

        Args:
            item (BaseTaskItem): tree item to select.
        """
        self._current_tree_item = item

    def get_current_tree_item(self):
        """Get currently selected tree item.

        Returns:
            (BaseTaskItem or None): current selected item, if there is one.
        """
        return self._current_tree_item

    ### properties ###
    @property
    def field_filters_dict(self):
        """Get dict of all field filters.

        Returns:
            (dict(str, BaseFilter)): dictionary of all tree field filters.
        """
        # TODO: may need to change this to include FilterType.GLOBAL types
        # as well? Not sure how we're planning to use that
        return self._filterer.get_filters_dict(self._filter_type)

    @property
    def field_filter(self):
        """Get active field filter, which is applied to the outliner itself.

        Returns:
            (BaseFilter): field filter.
        """
        if self._active_field_filter:
            return self._active_field_filter
        return convert_filter(NoFilter(), self._filter_type)

    @property
    def combined_filter(self):
        """Get combination of field filter and tree item filter.

        Note that the tree item filter has TREE filter_type while the
        field filter should have type self._filter_type, so we will need
        to convert to ensure the combined filter has self._filter_type.

        Returns:
            (BaseFilter): combined filter, with type self._filter_type.
        """
        if self._combined_filter is not None:
            return self._combined_filter
        if self._filtered_tree_items:
            if self._tree_item_filter is None:
                self._tree_item_filter = FilterByItem(
                    list(self._filtered_tree_items)
                )
            converted_tree_filter = convert_filter(
                self._tree_item_filter,
                self._filter_type,
            )
            self._combined_filter = converted_tree_filter & self.field_filter
            return self._combined_filter
        return self.field_filter

    ### Field Filter ###
    def get_field_filter(self, filter_path):
        """Get field filter by name.

        Args:
            filter_path (list(str)): path to filter, including name.

        Returns:
            (BaseFilter or None): field filter, if found.
        """
        return self._filterer.get_filter(self._filter_type, filter_path)

    def set_active_field_filter(self, field_filter):
        """Set active field filter.

        Args:
            field_filter (BaseFilter or None): the field filter to set active.
                If None, delete the filter.
        """
        self._active_field_filter = field_filter
        self._combined_filter = None
        self._project_user_prefs.set_attribute(
            [self._name, self.ACTIVE_FIELD_FILTER_PREF],
            field_filter.name if field_filter is not None else None,
        )

    def get_filters_dict(self, filter_type=None, filter_path=None):
        """Get filters dict for given filter type and path

        Args:
            filter_type (FilterType or None): filter type, if restricting.
            filter_path (list(str) or None): path to filters, if not saved
                directly under the filter_type category. If this path ends with
                the name of a filter, the final element of the list is ignored
                and the returned value is just the dict that filter lives in.

        Returns:
            (dict(str, BaseFilter) or None): filters dict for given type and
                path, if found. This may include nested filters.
        """
        return self._filterer.get_filters_dict(filter_type, filter_path)

    ### Field Filter Edits ###
    def add_field_filter(self, field_filter, filter_path):
        """Add given field filter.

        Args:
            field_filter (BaseFilter): the field filter to add.
            filter_path (list(str)): path to save filter under, including name.
        """
        AddFilterEdit.create_and_run(
            self._filterer,
            self._filter_type,
            filter_path,
            field_filter,
        )
        # self._filterer.add_filter(FilterType.TREE, field_filter)

    def modify_field_filter(
            self,
            old_filter_path,
            field_filter,
            new_filter_path=None):
        """Modify given field filter.

        Args:
            old_filter_path (list(str)): old path of filter we're modifying.
            field_filter (BaseFilter): the field filter after modification.
            new_filter_path (list(str)): new path of filter, if changed.
        """
        ModifyFilterEdit.create_and_run(
            self._filterer,
            self._filter_type,
            old_filter_path,
            field_filter,
            new_filter_path=new_filter_path,
        )
        old_name = old_filter_path[-1]
        # ensure filter is set as active if the one it replaced was active
        if (self._active_field_filter is not None and
                self._active_field_filter.name == old_name):
            self.set_active_field_filter(field_filter)

    def remove_field_filter(self, filter_path):
        """Remove field filter with given name.

        Args:
            filter_path (list(str)): path of filter to remove.
        """
        RemoveFilterEdit.create_and_run(
            self._filterer,
            self._filter_type,
            filter_path,
        )
