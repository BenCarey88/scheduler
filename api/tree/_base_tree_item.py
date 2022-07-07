"""Base tree item class."""

from collections import OrderedDict
from contextlib import contextmanager

from scheduler.api.common.object_wrappers import Hosted, MutableAttribute
from scheduler.api.constants import TASK_COLORS
from scheduler.api.serialization.serializable import NestedSerializable


class BaseTreeItem(Hosted, NestedSerializable):
    """Base class representing a tree item."""
    TREE_PATH_SEPARATOR = "/"
    DEFAULT_NAME = "tree_item"

    # TODO: remove id argument
    def __init__(self, name, parent=None, id=None):
        """Initialise tree item class.

        Args:
            name (str): name of tree item.
            parent (Task or None): parent of current item, if it's not a root.
            id (uuid4 or None): id of tree item. If not given, we create one.
                This argument allows us to create a new tree item but treat it
                as if it's the same as an old one (eg. if we want to change a
                Task to a TaskCategory).
        """
        super(BaseTreeItem, self).__init__()
        self._name = MutableAttribute(name, "name")
        self._parent = MutableAttribute(parent, "parent")
        self._children = OrderedDict()
        # base class must be overridden, has no allowed child types.
        self._allowed_child_types = []

    # TODO: this is only here so it can be accessed in the drag-drop stuff to find
    # the root of any model bc we're into the super-hacky just get something that
    # works stage of release1. We can probably remove this function (and maybe
    # replace some of that functionality with the tree manager?)
    @property
    def root(self):
        """Get root of tree.

        Returns:
            (TaskRoot): root tree item.
        """
        if self.parent:
            return self.parent.root
        return self

    @property
    def name(self):
        """Get item name.

        Returns:
            (str): item's name.
        """
        return self._name.value

    @property
    def parent(self):
        """Get parent item.

        Returns:
            (BaseTreeItem or None): parent item, if one exists.
        """
        return self._parent.value

    @property
    def path_list(self):
        """Get path to self from root tree item as list.

        Returns:
            (list(str)): list of names of ancestors.
        """
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return path

    @property
    def path(self):
        """Get path to self from root tree item as string.

        Returns:
            (str): path with names of all ancestors.
        """
        return self.TREE_PATH_SEPARATOR.join(self.path_list)

    # TODO: does this belong here?
    @property
    def color(self):
        """Get color of tree item.

        Returns:
            (tuple(int) or None): rgb color of item, if defined.
        """
        if self.name in TASK_COLORS:
            return TASK_COLORS.get(self.name)
        if self.parent:
            return self.parent.color
        return None

    def __str__(self):
        """Get string representation of self.

        Returns:
            (str): string repr of self.
        """
        return self.path

    @contextmanager
    def filter_children(self, filters):
        """Contextmanager to filter _children dict temporarily.

        This uses the child filters defined in the filters module.

        Args:
            filters (list(BaseFilter)): types of filtering required.
        """
        _children = self._children
        try:
            for child_filter in filters:
                self._children = child_filter.filter_function(
                    self._children,
                    self
                )
            yield
        finally:
            self._children = _children

    def get_child(self, name):
        """Get child by name.

        Args:
            name (str): name of child.

        Returns:
            (BaseTreeItem or None): child, if one by that name exits.
        """
        return self._children.get(name, None)

    def get_child_at_index(self, index):
        """Get child by index.

        Args:
            index (int): index of child.

        Returns:
            (BaseTreeItem or None): child, if one of that index exits.
        """
        if 0 <= index < len(self._children):
            return list(self._children.values())[index]
        return None

    def get_all_children(self):
        """Get all children of this item.

        Returns:
            (list(BaseTreeItem)): list of all children.
        """
        return list(self._children.values())

    def get_filtered_children(self, filters):
        """Get children of this item, using given filters.

        Returns:
            (list(BaseTreeItem)): list of filtered children.
        """
        with self.filter_children(filters):
            return self.get_all_children()

    def get_all_siblings(self):
        """Get all siblings of this item.

        Returns:
            (list(BaseTreeItem)): list of sibling items of this item.
        """
        if self.parent:
            return [
                child
                for child in self.parent.get_all_children()
                if child != self
            ]
        return []

    def get_all_descendants(self):
        """Get all descendants of item.

        Returns:
            (list(BaseTreeItem)): list of descendants.
        """
        descendants = self.get_all_children()
        for child in self.get_all_children():
            descendants.extend(child.get_all_descendants())
        return descendants

    def iter_descendants(self):
        """Iterate through all descendants of item.

        Yields:
            (BaseTreeItem): descendants.
        """
        for child in self.get_all_children():
            yield child
            for descendant in child.iter_descendants():
                yield descendant

    def iter_ancestors(self, reversed=False, strict=False):
        """Iterate through ancestors of this item, from oldest downwards.

        Args:
            reversed (bool): if True, iter from lowest upwards.
            strict (bool): if True, don't include this item in the iteration.

        Yields:
            (BaseTreeItem): ancestor items (including this one).
        """
        if reversed and not strict:
            yield self
        if self.parent:
            for ancestor in self.parent.iter_ancestors(reversed=reversed):
                yield ancestor
        if not reversed and not strict:
            yield self

    def get_family(self):
        """Get tree family members of this item with same class type.

        This iterates through ancestors and children of this item (and children
        of those ancestors) and adds them to the return list, stopping each
        branch of iteration when it meets a member of a different class type.

        Returns:
            (list(BaseTreeItem)): list of family members with same class type.
                List will include the current item.
        """
        current_item = self
        while isinstance(current_item.parent, self.__class__):
            current_item = current_item.parent
        return [current_item] + [
            item for item in current_item.get_all_descendants()
            if isinstance(item, self.__class__)
        ]

    def num_children(self):
        """Get number of children of this item.

        Returns:
            (int): number of children.
        """
        return len(self._children)

    def num_descendants(self):
        """Get number of descendants of this item.

        Returns:
            (int): number of descendants.
        """
        return sum([
            (child.num_descendants() + 1) for child in self._children.values()
        ])

    def index(self):
        """Get index of this item as a child of its parent.

        Wrapped to catch ValueError exceptions, in case of race conditions,
        ie. this has been deleted from its parent list during the course of
        this function being called.

        Returns:
            (int or None): index of this item, or None if it has no parent.
        """
        if not self.parent:
            return None
        try:
            return self.parent.get_all_children().index(self)
        except ValueError:
            return None

    def is_leaf(self):
        """Return whether or not this item is a leaf (ie has no children).

        Returns:
            (bool): True if this is a leaf, else False.
        """
        return not bool(self._children)

    def is_ancestor(self, other_tree_item):
        """Check if this item is an ancestor of another item.

        Args:
            other_tree_item (BaseTreeItem): other tree item to compare to.

        Returns:
            (bool): True if this is an ancestor of other_tree_item.
        """
        return other_tree_item.path.startswith(self.path)

    def get_descendants_with_incorrect_parents(
            self,
            parent=None,
            incorrect_children_list=None,
            check_self=False):
        """Find any descendants with missing / incorrect parents.

        Useful for debugging purposes.

        Args:
            check_self (bool): if True, check if this has correct parent too.
            parent (BaseTreeItem): parent to check against, if one exists.
            incorrect_children_list (list): list of children with missing
                or incorrect parents.

        Returns:
            (list(str)): list of names of descendents with missing or incorrect
                parents.
        """
        if incorrect_children_list is None:
            incorrect_children_list = []
        if check_self and self.parent != parent:
            incorrect_children_list.append(self.name)
        for child in self.get_all_children():
            child.get_descendants_with_incorrect_parents(
                parent=self,
                incorrect_children_list=incorrect_children_list,
                check_self=True,
            )
        return incorrect_children_list

    def print(self, include_children=True, depth=0):
        """Print tree item, for debugging purposes.

        Args:
            include_children (bool): if True, print descendants as well.
            depth (int): recursive depth of function, usedd to determine
                indentation.
        """
        print (depth * "    ", self.name)
        if include_children:
            for child in self.get_all_children():
                child.print(True, depth + 1)
