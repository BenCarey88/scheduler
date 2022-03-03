"""Tree manager class to manage filtering tree items for each model.

Each tab is intended to have its own tree manager class. This allows
us to maintain ui-specific properties for each tree item without
editing the underlying tree item data, eg. whether or not the item
is being filtered for in the current tab.
"""

from scheduler.api.common import user_prefs
from scheduler.api.tree.filters import NoFilter, FilterByItem


class TreeManager(object):
    """Tree manager class to maintain ui attributes for each tree item.

    This stores attributes for each item in internal data dicts, keyed by tree
    item.

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

    def __init__(self, name, user_prefs, tree_root):
        """Initialise tree manager. Note that this class actually has no
        knowledge of the tree item itself, so needs to be used in conjunction
        with a tree root.

        Args:
            name (str): name of tree manager.
            user_prefs (_ProjectUserPrefs): project user prefs class.
            tree_root (TaskRoot): root task object.

        Attributes:
            _tree_data (dict(str, dict)): additional tree data for each item.
            _filtered_items (set(str)): set of items we're filtering out.
        """
        self._name = name
        self._project_user_prefs = user_prefs
        self._tree_root = tree_root
        self._tree_data = {}
        self._filtered_items = set()
        self.setup_from_user_prefs()

    def setup_from_user_prefs(self):
        """Setup filtering based on user prefs."""
        filter_attrs = self._project_user_prefs.get_attribute(
            [self._name, self.FILTERED_TASKS_PREF], {}
        )
        for tree_item, attr_dict in filter_attrs.items():
            if tree_item and attr_dict:
                for attr, value in attr_dict.items():
                    self._tree_data.setdefault(tree_item, {})[attr] = value

    def has_attribute(self, tree_item, attribute):
        """Check if tree item already has attribute defined in internal dict.

        Args:
            tree_item (BaseTreeItem): tree item to query for.
            atttribute (str): attribute name.

        Returns:
            (bool): whether or not given attribute is currently defined in
                internal dict.
        """
        return attribute in self._tree_data.setdefault(tree_item, {})

    def get_attribute(self, tree_item, attribute):
        """Get the attribute for the given tree item.

        Args:
            tree_item (BaseTreeItem): tree item to query for.
            atttribute (str): attribute name.

        Returns:
            (variant): value of attribute for given item.
        """
        item_dict = self._tree_data.setdefault(tree_item, {})
        default = self.ATTRIBUTE_DEFAULTS.get(attribute)
        return item_dict.setdefault(attribute, default)

    def set_attribute(self, tree_item, attribute,  value):
        """Set the attribute for the given tree item.

        Args:
            tree_item (BaseTreeItem): tree item to set attribute for.
            atttribute (str): attribute name.
            value (variant): value to set.
        """
        if attribute in self.USER_PREFS_ATTRIBUTES:
            default = self.ATTRIBUTE_DEFAULTS.get(attribute)
            self._project_user_prefs.set_attribute(
                [self._name, self.FILTERED_TASKS_PREF, tree_item, attribute],
                value,
                default
            )
        item_dict = self._tree_data.setdefault(tree_item, {})
        item_dict[attribute] = value

    def is_filtered_out(self, tree_item):
        """Check if the given tree item is filtered out.

        Args:
            tree_item (BaseTreeItem): tree item to query.

        Returns:
            (bool): whether or not the given item is being filtered out.
        """
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
            tree_item (BaseTreeItem): tree item to query.

        Returns:
            (bool): whether or not the given item is selected for filtering.
        """
        return self.get_attribute(tree_item, self.IS_SELECTED_FOR_FILTERING)

    def siblings_are_selected_for_filtering(self, tree_item):
        """Check if all this tree_item's siblings are selected for filtering.

        Args:
            tree_item (BaseTreeItem): tree item to query.

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
            tree_item (BaseTreeItem): tree item to query.

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

    def is_expanded(self, tree_item):
        """Check if the given tree item has been expanded in the outliner.

        Args:
            tree_item (BaseTreeItem): tree item to query.

        Returns:
            (bool): whether or not the given item is expanded.
        """
        return self.get_attribute(tree_item, self.IS_EXPANDED)

    def filter_item(self, tree_item, from_user_selection=True):
        """Add tree item to filter list.

        Args:
            tree_item (BaseTreeItem): tree item to filter out.
            from_user_selection (bool): if True, this is being set because the
                user has selected to filter out the given item. Otherwise,
                this is being called recursively because one of this item's
                ancestors has been selected for filtering.
        """
        if from_user_selection:
            self.set_attribute(tree_item, self.IS_SELECTED_FOR_FILTERING, True)
        self.set_attribute(tree_item, self.IS_FILTERED_OUT, True)
        self._filtered_items.add(tree_item)
        for child in tree_item.get_all_children():
            self.filter_item(child, from_user_selection=False)

    def unfilter_item(self, tree_item, from_user_selection=True):
        """Remove tree item from filter list.

        Args:
            tree_item (BaseTreeItem): tree item to remove filter from.
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
        self._filtered_items.discard(tree_item)
        for child in tree_item.get_all_children():
            self.unfilter_item(child, from_user_selection=False)

    def filter_ancestoral_siblings(self, tree_item):
        """Add all siblings of tree item and ancestors to filter list.

        Args:
            tree_item (BaseTreeItem): tree item to filter out.
        """
        for sibling in tree_item.get_all_siblings():
            self.filter_item(sibling)
        if tree_item.parent:
            self.filter_ancestoral_siblings(tree_item.parent)

    def unfilter_ancestoral_siblings(self, tree_item):
        """Remove all sibling of tree item and ancestors from filter list.

        Args:
            tree_item (BaseTreeItem): tree item to unfilter.
        """
        for sibling in tree_item.get_all_siblings():
            self.unfilter_item(sibling)
        if tree_item.parent:
            self.unfilter_ancestoral_siblings(tree_item.parent)

    def expand_item(self, tree_item, value):
        """Mark item as collapsed/expanded in the outliner.

        Args:
            tree_item (BaseTreeItem): tree item to expand or collapse.
            value (bool): the value to mark it as (True means expanded, False
                means collapsed).
        """
        self.set_attribute(tree_item, self.IS_EXPANDED, value)

    def set_expanded_from_filtered(self, item):
        """Set filtered items as collapsed and unfiltered as expanded.

        Args:
            item (BaseTreeItem): tree item to set from.
        """
        # TODO: was there a reason we didn't pass tree root to tree_manager?
        # feels like it would be useful to have
        if self.is_filtered_out(item):
            self.expand_item(item, False)
        else:
            self.expand_item(item, True)
            for child in item.get_all_children():
                self.set_expanded_from_filtered(child)

    @property
    def child_filter(self):
        """Get filter to filter children.

        Returns:
            (BaseFilter): filter to filter children with.
        """
        if self._filtered_items:
            return FilterByItem(list(self._filtered_items))
        return NoFilter()
