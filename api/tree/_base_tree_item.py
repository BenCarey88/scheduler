"""Base tree item class."""

from abc import ABC
from collections import OrderedDict
from contextlib import contextmanager
from uuid import uuid4

from scheduler.api.constants import TASK_COLOURS
from scheduler.api.edit.tree_edit import (
    AddChildrenEdit,
    InsertChildrenEdit,
    ModifyChildrenEdit,
    MoveChildrenEdit,
    RemoveChildrenEdit,
    RenameChildrenEdit,
)
from .exceptions import (
    ChildNameError,
    DuplicateChildNameError,
    MultipleParentsError,
    UnallowedChildType,
)


class BaseTreeItem(ABC):
    """Base class representing a tree item."""

    TREE_PATH_SEPARATOR = "/"

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
        self._name = name
        self.parent = parent
        self._children = OrderedDict()
        self._register_edits = True
        self.id = id or uuid4()
        # base class must be overridden, has no allowed child types.
        # TODO: this feels like a class property rather than an instance one
        self.allowed_child_types = []

    def __eq__(self, tree_item):
        """Check if this item is equal to another item.

        Returns:
            (bool): whether the items are equal.
        """
        if isinstance(tree_item, BaseTreeItem):
            return self.id == tree_item.id
        return False

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
            RenameChildrenEdit.create_and_run(
                parent,
                {self.name: new_name},
                register_edit=self._register_edits,
            )

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
    def colour(self):
        """Get colour of tree item.

        Returns:
            (tuple(int) or None): rgb colour of item, if defined.
        """
        if self.name in TASK_COLOURS:
            return TASK_COLOURS.get(self.name)
        if self.parent:
            return self.parent.colour
        return None

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

    def create_child(
            self,
            name,
            child_type=None,
            index=None,
            **kwargs):
        """Create child item and add to children dict.

        Args:
            name (str): name of child.
            child_type (class or None): class to use for child init. If None,
                use current class.
            index (int or None): if given, insert child at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to child init.

        Raises:
            (DuplicateChildNameError): if a child with given name already
                exists.
            (UnallowedChildType): if the child_type is not allowed.

        Returns:
            (BaseTreeItem): newly created child. In subclasses, this will use
                the type of the subclass.
        """
        if name in self._children:
            raise DuplicateChildNameError(self.name, name)
        child_type = child_type or self.__class__
        if child_type not in self.allowed_child_types:
            raise UnallowedChildType(self.__class__, child_type)
        child = child_type(name, parent=self, **kwargs)
        if index is None:
            index = len(self._children)
        if index > len(self._children):
            raise IndexError("Index given is larger than number of children.")
        InsertChildrenEdit.create_and_run(
            self,
            {name: (index, child)},
            register_edit=self._register_edits,
        )
        return child

    def create_new_child(
            self,
            default_name="child",
            child_type=None,
            index=None,
            **kwargs):
        """Create a new child with a default name.

        This adds a number at the end of the name to allow us to add mutliple
        new children with different names.

        Args:
            default_name (str): the default name to use (before appending
                the number).
            child_type (class or None): class to use for child init. If None,
                use current class.
            index (int or None): if given, insert child at given index, else
                add at end of _children dict.
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
            index=index,
            **kwargs
        )

    def add_child(self, child, index=None):
        """Add an existing child to this item's children dict.

        Args:
            child (BaseTreeItem): child item to add.
            index (int or None): if given, insert child at given index, else
                add at end of _children dict.

        Raises:
            (DuplicateChildNameError): if a child with given name already
                exists.
            (MultipleParentsError): if the child has a different tree item as
                a parent.
        """
        if child.name in self._children:
            raise DuplicateChildNameError(self.name, child.name)
        if type(child) not in self.allowed_child_types:
            raise UnallowedChildType(self.__class__, type(child))
        if not child.parent:
            child.parent = self
        if child.parent != self:
            raise MultipleParentsError(
                "child {0} has incorrect parent: {1} instead of {2}".format(
                    child.name, child.parent.name, self.name
                )
            )
        if index is None:
            index = len(self._children)
        if index > len(self._children):
            raise IndexError("Index given is larger than number of children.")
        InsertChildrenEdit.create_and_run(
            self,
            {child.name: (index, child)},
            register_edit=self._register_edits,
        )

    def create_sibling(self, name, index=None, **kwargs):
        """Create sibling item for self.

        Args:
            name (str): the name of the sibling.
            index (int or None): if given, insert sibling at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to sibling init.

        Returns:
            (BaseTreeItem or None): newly created sibling, if one could be
                created, else None. In subclasses, this will use the type
                of the subclass.
        """
        if not self.parent:
            return None
        return self.parent.create_child(
            name,
            child_type=self.__class__,
            index=index,
            **kwargs
        )

    def create_new_sibling(self, default_name="sibling", index=None, **kwargs):
        """Create sibling item for self.

        Args:
            default_name (str): the default name to use (before appending
                the number).
            index (int or None): if given, insert sibling at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to sibling init.

        Returns:
            (BaseTreeItem or None): newly created sibling, if one could be
                created, else None. In subclasses, this will use the type
                of the subclass.
        """
        if not self.parent:
            return None
        return self.parent.create_new_child(
            default_name,
            child_type=self.__class__,
            index=index,
            **kwargs
        )

    def add_sibling(self, sibling, index=None):
        """Add sibling item for self.

        Args:
            sibling (BaseTreeItem): the sibling to add.
            index (int or None): if given, insert sibling at given index, else
                add at end of _children dict.
        """
        if not self.parent:
            return
        self.parent.add_child(sibling, index=index)

    def remove_child(self, name):
        """Remove an existing child from this item's children dict.

        Args:
            name (str): name of child item to remove.
        """
        if name in self._children.keys():
            RemoveChildrenEdit.create_and_run(
                self,
                [name],
                register_edit=self._register_edits,
            )

    def remove_children(self, names):
        """Remove existing children from this item's children dict.

        Args:
            name (list(str)): name of child items to remove.
        """
        names = [name for name in names if name in self._children.keys()]
        RemoveChildrenEdit.create_and_run(
            self,
            names,
            register_edit=self._register_edits,
        )

    def replace_child(self, name, new_child):
        """Replace child at given name with new_child.

        Args:
            name (str): name of child item to replace.
            new_child (BaseTreeItem): new tree item to replace the original
                child.

        Raises:
            (ChildNameError): if new_child has different name to old one.
            (MultipleParentsError): if the child has a different tree item as
                a parent.
        """
        if name != new_child.name:
            raise ChildNameError(
                "Can't replace child {0} with new child of "
                "different name {1}".format(name, new_child.name)
            )
        if type(new_child) not in self.allowed_child_types:
            raise UnallowedChildType(self.__class__, type(new_child))
        if not new_child.parent:
            new_child.parent = self
        if new_child.parent != self:
            raise MultipleParentsError(
                "child {0} has incorrect parent: {1} instead of {2}".format(
                    new_child.name, new_child.parent.name, self.name
                )
            )
        ModifyChildrenEdit.create_and_run(
            self,
            {name: new_child},
            register_edit=self._register_edits,
        )

    def move(self, new_index):
        """Move this item to new index in parent's _children dict.

        Args:
            new_index (int): new index to move to.
        """
        if not self.parent:
            return
        if new_index >= self.parent.num_children() or new_index < 0:
            return
        if new_index == self.index():
            return
        MoveChildrenEdit.create_and_run(
            self.parent,
            {self.name: new_index},
            register_edit=self._register_edits,
        )

    def change_child_tree_type(self, child_name, new_tree_class):
        """Attempt to change child tree class to a different tree class.

        Args:
            child_name (str): name of child to change.
            new_tree_class (class): new tree class to use for child.

        Raises:
            (UnallowedChildType): if the new_tree_class is not an allowed
                child type of the this class OR if some of the children
                of the given child are unallowed child types for the new
                tree class.
        """
        if new_tree_class not in self.allowed_child_types:
            raise UnallowedChildType(self.__class__, new_tree_class)
        child = self.get_child(child_name)
        if not child or isinstance(child, new_tree_class):
            return
        new_child = new_tree_class(child_name)
        for grandchild in child.get_all_children():
            grandchild_class = type(grandchild)
            if grandchild_class not in new_child.allowed_child_types:
                raise UnallowedChildType(grandchild_class)
            grandchild_copy = grandchild_class.from_dict(
                grandchild.to_dict()
            )
            new_child._children[grandchild_copy.name] = grandchild_copy
        self.replace_child(child_name, new_child)

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
