"""Base tree item class."""

from abc import ABC
from collections import OrderedDict
from contextlib import contextmanager

from scheduler.api.utils import catch_exceptions
from .tree_edits import BaseTreeEdit, EditOperation


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
    of the current item. However, most of its methods include a child_dict arg
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
        self._register_edits = False

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
            name_edit = BaseTreeEdit(
                diff_dict=OrderedDict([(self.name, new_name)]),
                op_type=EditOperation.RENAME,
                register_edit=self._register_edits,
            )
            name_edit(parent)

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
        return "|".join(self.path_list)

    def create_child(
            self,
            name,
            child_type=None,
            **kwargs):
        """Create child item and add to children dict.

        Args:
            name (str): name of child.
            child_type (class or None): class to use for child init. If None,
                use current class.
            **kwargs: kwargs to be passed to child init.

        Raises:
            (DuplicateChildNameError): if a child with given name already exists.

        Returns:
            (BaseTreeItem): newly created child. In subclasses, this will use
                the type of the subclass.
        """
        if name in self._children:
            raise DuplicateChildNameError(self.name, name)
        child_type = child_type or self.__class__
        child = child_type(name, parent=self, **kwargs)
        add_child_edit = BaseTreeEdit(
            diff_dict=OrderedDict([(name, child)]),
            op_type=EditOperation.ADD,
            register_edit=self._register_edits,
        )
        add_child_edit(self)
        return child

    def create_new_child(
            self,
            default_name="child",
            child_type=None,
            **kwargs):
        """Create a new child with a default name.

        This adds a number at the end of the name to allow us to add mutliple
        new children with different names.

        Args:
            default_name (str): the default name to use (before appending
                the number).
            child_type (class or None): class to use for child init. If None,
                use current class.
            **kwargs: kwargs to be passed to child init.

        Returns:
            (BaseTreeItem): newly created child. In subclasses, this will use
                the type of the subclass.
        """
        suffix = 1
        while (default_name + str(suffix).zfill(3)) in self._children.keys():
            suffix += 1
        return self.create_child(
            default_name + str(suffix).zfill(3),
            child_type,
            **kwargs
        )

    def add_child(self, child):
        """Add an existing child to this item's children dict.

        Args:
            child (BaseTreeItem): child item to add.

        Raises:
            (DuplicateChildNameError): if a child with given name already exists.
            (MultipleParentsError): if the child has a different tree item as
                a parent.
        """
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
        add_child_edit = BaseTreeEdit(
            diff_dict=OrderedDict([(child.name, child)]),
            op_type=EditOperation.ADD,
            register_edit=self._register_edits,
        )
        add_child_edit(self)

    def create_sibling(self, name, **kwargs):
        """Create sibling item for self.

        Args:
            name (str): the name of the sibling.
            **kwargs: kwargs to be passed to sibling init.

        Returns:
            (BaseTreeItem): newly created sibling. In subclasses, this will use
                the type of the subclass.
        """
        if not self.parent:
            return None
        return self.parent.create_child(
            name,
            child_type=self.__class__,
            **kwargs
        )

    def create_new_sibling(self, default_name="sibling", **kwargs):
        """Create sibling item for self.

        Args:
            default_name (str): the default name to use (before appending
                the number).
            **kwargs: kwargs to be passed to sibling init.

        Returns:
            (BaseTreeItem): newly created sibling. In subclasses, this will use
                the type of the subclass.
        """
        if not self.parent:
            return None
        return self.parent.create_new_child(
            default_name,
            child_type=self.__class__,
            **kwargs
        )

    def add_sibling(self, sibling):
        """Create sibling item for self.

        Args:
            sibling (BaseTreeItem): the sibling to add.
        """
        if not self.parent:
            return None
        self.parent.add_child(sibling)

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
            remove_child_edit = BaseTreeEdit(
                diff_dict=OrderedDict([(name, None)]),
                op_type=EditOperation.REMOVE,
                register_edit=self._register_edits,
            )
            remove_child_edit(self)

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

    @catch_exceptions(ValueError)
    def index(self, child_dict=None):
        """Get index of this item as a child of its parent.

        Wrapped to catch ValueError exceptions, in case of race conditions,
        ie. this has been deleted from its parent list during the course of
        this function being called.

        child_dict (OrderedDict or None): dict of parent's to use as
            child_dict. If None, use parent._children.

        Returns:
            (int or None): index of this item, or None if it has no parent.
        """
        if not self.parent:
            return None
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

    def open_edit_registry(self):
        """Set all children editable so that users can undo and redo edits."""
        self._register_edits = True
        for child in self.get_all_children():
            child.open_edit_registry()
