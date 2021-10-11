"""Base tree item class."""

from abc import ABC
from collections import OrderedDict
from contextlib import contextmanager


class DuplicateChildNameError(Exception):
    """Exception for two cildren having the same name."""
    def __init__(self, tree_item_name, child_item_name):
        """Initialise exception.

        Args:
            tree_item_name (str): name of tree item we're adding child to.
            child_item_name (str): name of child.
        """
        message = "child of {0} with name {1} already exists".format(
            tree_item_name, child_item_name
        )
        super(DuplicateChildNameError, self).__init__(message)


class MultipleParentsError(Exception):
    """Exception for when new child does not have current item as a parent."""
    pass


class BaseTreeItem(ABC):
    """Base class representing a tree item.
    
    This class has a _children dict attribute representing the list of children
    of the current item. However, all its methods include a child_dict arg
    which allow subclasses to pass in a second dictionary of children to use,
    enabling multiple types of children. It is assumed that this child_dict
    will always be a subdict of self._children.
    """
    
    def __init__(self, name, parent=None):
        """Initialise tree item class.

        Args:
            name (str): name of tree item.
            parent (Task or None): parent of current item, if it's not a root.
        """
        self._name = name
        self.parent = parent
        self._children = OrderedDict()
        self.pruned = False

    @property
    def name(self):
        """Get item name.

        Returns:
            (str): item's name.
        """
        return self._name

    @name.setter
    def name(self, new_name):
        """Set item name.

        This setter also updates the item's name in its parent's child dict.

        Args:
            new_name (str): new item name.

        Raises:
            (DuplicateChildNameError): if the new name is the same as one of its
                siblings.
        """
        parent = self.parent
        if parent:
            if parent.get_child(new_name):
                raise DuplicateChildNameError(parent.name, new_name)
            # replace parent's child item key by cycling through ordered dict
            for i in range(len(parent._children)):
                k, v = parent._children.popitem(last=False)
                if k == self._name:
                    k = new_name
                parent._children[k] = v
        self._name = new_name

    @contextmanager
    def filter_children(self, *filters):
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

    def create_child(
            self,
            name,
            child_type=None,
            child_dict=None,
            **kwargs):
        """Create child item and add to children dict.

        Args:
            name (str): name of child.
            child_type (class or None): class to use for child init. If None,
                use current class.
            child_dict (OrderedDict or None): dict to add child to. If None,
                use self._children.
            **kwargs: kwargs to be passed to child init.

        Raises:
            (DuplicateChildNameError): if a child with given name already exists.

        Returns:
            (BaseTreeItem): newly created child. In subclasses, this will use
                the type of the subclass.
        """
        child_dict = child_dict or self._children
        if name in child_dict:
            raise DuplicateChildNameError(self.name, name)
        child_type = child_type or self.__class__
        child = child_type(name, parent=self, **kwargs)
        self._children[name] = child
        return child

    def add_child(self, child, child_dict=None):
        """Add an existing child to this item's children dict.

        Args:
            child (BaseTreeItem): child item to add.
            child_dict (OrderedDict or None): dict to add child to. If None,
                use self._children.

        Raises:
            (DuplicateChildNameError): if a child with given name already exists.
            (MultipleParentsError): if the child has a different tree item as
                a parent.
        """
        child_dict = child_dict or self._children
        if child.name in self._children:
            raise DuplicateChildNameError(self.name, child.name)
        if not child.parent:
            child.parent = self
        if child.parent != self:
            raise MultipleParentsError(
                "child {0} has incorrect parent: {1} instead of {2}".format(
                    child.name, child.parent.name, self.name
                )
            )
        child_dict[child.name] = child

    def remove_child(self, name, child_dict=None):
        """Remove an existing child from this item's children dict.

        Args:
            name (str): name of child item to remove.
            child_dict (OrderedDict or None): dict to check if child is in.
                We still remove the child from self._children as it's
                assumed the given child_dict will be a subset of
                self._children.
        """
        child_dict = child_dict or self._children
        if name in child_dict.keys():
            # edit self._children by cycling through dict
            for i in range(len(self._children)):
                k, v = self._children.popitem(last=False)
                if k != name:
                    self._children[k] = v
                else:
                    v.pruned = True

    def get_child(self, name, child_dict=None):
        """Get child by name.

        Args:
            name (str): name of child.
            child_dict (OrderedDict or None): dict to get child from. If None,
                use self._children.

        Returns:
            (BaseTreeItem or None): child, if one by that name exits.
        """
        child_dict = child_dict or self._children
        return child_dict.get(name, None)

    def get_child_at_index(self, index, child_dict=None):
        """Get child by index.

        Args:
            index (int): index of child.
            child_dict (OrderedDict or None): dict to get child from. If None,
                use self._children.

        Returns:
            (Task or None): child, if one of that index exits.
        """
        child_dict = child_dict or self._children
        if 0 <= index < len(child_dict):
            return list(child_dict.values())[index]
        return None

    def get_all_children(self, child_dict=None):
        """Get all children of this item.

        Args:
            child_dict (OrderedDict or None): dict to get children from. If
                None, use self._children.

        Returns:
            (list(Task)): list of all children.
        """
        child_dict = child_dict or self._children
        return list(child_dict.values())

    def num_children(self, child_dict=None):
        """Get number of children of this item.

        child_dict (OrderedDict or None): dict to get children from. If None,
                use self._children.

        Returns:
            (int): number of children.
        """
        child_dict = child_dict or self._children
        return len(child_dict)

    def num_descendants(self, child_dict=None):
        """Get number of descendants of this item.

        child_dict (OrderedDict or None): dict to get children from. If None,
                use self._children.

        Returns:
            (int): number of descendants.
        """
        child_dict = child_dict or self._children
        return sum(
            [(child.num_descendants() + 1) for child in child_dict.values()]
        )

    def index(self, child_dict=None):
        """Get index of this item as a child of its parent.

        child_dict (OrderedDict or None): dict of parent's to use as
            child_dict. If None, use parent._children.

        Returns:
            (int): index of this item.
        """
        if not self.parent:
            return 0
        else:
            return self.parent.get_all_children(child_dict).index(self)

    def is_leaf(self, child_dict=None):
        """Return whether or not this item is a leaf (ie has no children).

        child_dict (OrderedDict or None): dict to search for children in. If
            None, use self._children.

        Returns:
            (bool): True if this is a leaf, else False.
        """
        child_dict = child_dict or self._children
        return not bool(child_dict)
