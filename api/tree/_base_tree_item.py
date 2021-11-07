"""Base tree item class."""

from abc import ABC
from collections import OrderedDict
from contextlib import contextmanager

from scheduler.api.edit.tree_edit import BaseTreeEdit, EditOperation
from scheduler.api.utils import catch_exceptions

from .exceptions import DuplicateChildNameError, MultipleParentsError


class BaseTreeItem(ABC):
    """Base class representing a tree item."""

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

    def remove_child(self, name):
        """Remove an existing child from this item's children dict.

        Args:
            name (str): name of child item to remove.
        """
        if name in self._children.keys():
            remove_child_edit = BaseTreeEdit(
                diff_dict=OrderedDict([(name, None)]),
                op_type=EditOperation.REMOVE,
                register_edit=self._register_edits,
            )
            remove_child_edit(self)

    def remove_children(self, names):
        """Remove existing children from this item's children dict.

        Args:
            name (list(str)): name of child items to remove.
        """
        names = [name for name in names if name in self._children.keys()]
        remove_children_edit = BaseTreeEdit(
            diff_dict=OrderedDict([(name, None) for name in names]),
            op_type=EditOperation.REMOVE,
            register_edit=self._register_edits,
        )
        remove_children_edit(self)

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
            (Task or None): child, if one of that index exits.
        """
        if 0 <= index < len(self._children):
            return list(self._children.values())[index]
        return None

    def get_all_children(self):
        """Get all children of this item.

        Returns:
            (list(Task)): list of all children.
        """
        return list(self._children.values())

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
        else:
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

    def open_edit_registry(self):
        """Set all children editable so that users can undo and redo edits."""
        self._register_edits = True
        for child in self.get_all_children():
            child.open_edit_registry()
