"""Tree manager class to manage tree items for each model.

Each tab is intended to have its own tree manager class. This allows
us to maintain ui-specific properties for each tree item without
editing the underlying tree item data, eg. whether or not the item
is being filtered for in the current tab.

Data for each tree item is maintained via its unique id.
"""

from scheduler.api.tree.filters import RemoveChildrenById
from scheduler.ui.constants import TASK_STATUS_CHECK_STATES


# TODO: I think the current plan is to massively extend this class so that
# most/all of the task operations done through the ui go through this class.
# In service of this we should split this out into a separate tree_manager
# directory, make a main tree manager class in it (defined in the __init__
# or in another module and imported into the __init__) and then have that
# own a separate filter_manager attribute that is effectively this class.
# (Or maybe it could subclass the filter manager?)
# basically there's gonna be a whole lot of functions (potentially a
# reimplementation of almost everything from BaseTreeItem and its subclasses??)
# so I want to spread it out if possible.
# QUESTION: should we still do that extension? very much an open q.

class TreeManager(object):
    """Tree manager class to maintain ui attributes for each tree item.

    This stores attributes for each item in internal data dicts, keyed by tree
    item id.

    Attributes:
        IS_SELECTED_FOR_FILTERING (bool): whether or not the user has selected
            to filter the current item out of the tree.
        IS_FILTERED_OUT (bool): whether or not the item should be filtered out
            of the tree (either because the user selected to filter it out, or
            because one of its ancestors has been selected to be filtered out).
    """
    IS_SELECTED_FOR_FILTERING = "is_selected_for_filtering"
    IS_FILTERED_OUT = "is_filtered_out"

    def __init__(self):
        """Initialise tree manager. Note that this class actually has no
        knowledge of the tree item itself, so needs to be used in conjunction
        with a tree root.

        Attributes:
            _tree_data (dict(str, dict)): additional tree data for each item,
                keyed by item id.
            _filtered_items (set(str)): set of ids of items we're filtering
                out.
        """
        self._tree_data = {}
        self._filtered_items = set()

    def get_attribute(self, tree_item, attribute, default):
        """Get the attribute for the given tree item.

        Args:
            tree_item (BaseTreeItem): tree item to query for.
            atttribute (str): attribute name.
            default (variant): default value.

        Returns:
            (variant): value of attribute for given item.
        """
        item_dict = self._tree_data.setdefault(tree_item.id, {})
        return item_dict.setdefault(attribute, default)

    def set_attribute(self, tree_item, attribute, value):
        """Set the attribute for the given tree item.

        Args:
            tree_item (BaseTreeItem): tree item to set attribute for.
            atttribute (str): attribute name.
            value (variant): value to set.
        """
        item_dict = self._tree_data.setdefault(tree_item.id, {})
        item_dict[attribute] = value

    def is_filtered_out(self, tree_item):
        """Check if the given tree item is filtered out.
        
        Args:
            tree_item (BaseTreeItem): tree item to query.

        Returns:
            (bool): whether or not the given item is being filtered out.
        """
        return self.get_attribute(
            tree_item,
            self.IS_FILTERED_OUT,
            False
        )

    def is_selected_for_filtering(self, tree_item):
        """Check if the given tree item has been selected for filtering.

        Args:
            tree_item (BaseTreeItem): tree item to query.

        Returns:
            (bool): whether or not the given item is selected for filtering.
        """
        return self.get_attribute(
            tree_item,
            self.IS_SELECTED_FOR_FILTERING,
            False
        )

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
        self._filtered_items.add(tree_item.id)
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

        # if given item is selected for filtering, can't unfilter so return
        if self.is_selected_for_filtering(tree_item):
            return

        self.set_attribute(tree_item, self.IS_FILTERED_OUT, False)
        self._filtered_items.discard(tree_item.id)
        for child in tree_item.get_all_children():
            self.unfilter_item(child, from_user_selection=False)

    @property
    def child_filter(self):
        """Get filter to filter children by id.

        Returns:
            (RemoveChildrenById or None): filter if any filtering needed.
        """
        if self._filtered_items:
            return RemoveChildrenById(list(self._filtered_items))
        return None
