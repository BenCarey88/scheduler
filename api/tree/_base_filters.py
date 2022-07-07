"""Base filters for children in tree models."""


from collections import OrderedDict


class BaseFilter(object):
    """Base filter (does nothing)."""
    def filter_function(self, child_dict, item):
        return child_dict


class NoFilter(BaseFilter):
    """Filter that does nothing."""

    def __bool__(self):
        """Override bool operator to return False.
        
        Returns:
            (bool): False (to reflect that this is an 'empty' filter).
        """
        return False

    def __nonzero__(self):
        """Override bool operator to return False (Python 2.x)
        
        Returns:
            (bool): False (to reflect that this is an 'empty' filter).
        """
        return False


class FullPrune(BaseFilter):
    """Filter to remove all children."""
    def filter_function(self, child_dict, item):
        return OrderedDict()


class KeepChildrenOfType(BaseFilter):
    """Filter to keep only the items of the given type."""

    def __init__(self, class_type):
        self.class_type = class_type

    def filter_function(self, child_dict, item):
        filtered_dict = OrderedDict()
        for key, value in child_dict.items():
            if type(value) == self.class_type:
                filtered_dict[key] = value
        return filtered_dict


class RemoveChildrenOfType(BaseFilter):
    """Filter to remove all items of the given type."""

    def __init__(self, class_type):
        self.class_type = class_type

    def filter_function(self, child_dict, item):
        filtered_dict = OrderedDict()
        for key, value in child_dict.items():
            # TODO replace all type() == comparisons with isinstance
            if type(value) != self.class_type:
                filtered_dict[key] = value
        return filtered_dict


class RemoveSubChildrenOfType(BaseFilter):
    """Filter to remove all children of items with the given type."""

    def __init__(self, class_type):
        self.class_type = class_type

    def filter_function(self, child_dict, item):
        if type(item) == self.class_type:
            return OrderedDict()
        return child_dict


class RemoveGivenChildren(BaseFilter):
    """Filter to remove the given children."""

    def __init__(self, specified_parent, children_to_remove):
        """Initialise filter.

        Args:
            specified_parent (BaseTreeItem): parent to restrict children of.
            children_to_keep (list(str)): names of children to keep for given
                parent.
        """
        self.specified_parent = specified_parent
        self.children_to_remove = children_to_remove

    def filter_function(self, child_dict, item):
        if item != self.specified_parent:
            return child_dict
        filtered_dict = OrderedDict()
        for key, value in child_dict.items():
            if key not in self.children_to_remove:
                filtered_dict[key] = value
        return filtered_dict


class RestrictToGivenChildren(BaseFilter):
    """Filter to remove all but the given children for specified parent."""

    def __init__(self, specified_parent, children_to_keep):
        """Initialise filter.

        Args:
            specified_parent (BaseTreeItem): parent to restrict children of.
            children_to_keep (list(str)): names of children to keep for given
                parent.
        """
        self.specified_parent = specified_parent
        self.children_to_keep = children_to_keep

    def filter_function(self, child_dict, item):
        if item != self.specified_parent:
            return child_dict
        filtered_dict = OrderedDict()
        for key, value in child_dict.items():
            if key in self.children_to_keep:
                filtered_dict[key] = value
        return filtered_dict


class FilterByItem(BaseFilter):
    """Filter to remove given items."""

    def __init__(self, items_to_remove):
        """Initialise filter.

        Args:
            items_to_remove (list(BaseTreeItem)): items to remove.
        """
        self._items_to_remove = items_to_remove

    def filter_function(self, child_dict, item):
        filtered_dict = OrderedDict()
        for key, value in child_dict.items():
            if value not in self._items_to_remove:
                filtered_dict[key] = value
        return filtered_dict
