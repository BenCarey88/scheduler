"""Tree edits to be applied to tree items."""

from collections import OrderedDict

from ._core_edits import CompositeEdit, SelfInverseSimpleEdit
from ._ordered_dict_edit import OrderedDictEdit, OrderedDictOp


class BaseTreeEdit(CompositeEdit):
    """Edit that can be called on a tree item."""

    def __init__(self, tree_item, diff_dict, op_type, register_edit=True):
        """Initialise base tree edit.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            diff_dict (OrderedDict): a dictionary representing modifications
                to the tree item's child dict. How to interpret this dictionary
                depends on the operation type.
            operation_type (OrderedDictOp): The type of edit operation to do.
            register_edit (bool): whether or not to register this edit.
        """
        self.diff_dict = diff_dict
        ordered_dict_edit = OrderedDictEdit(
            tree_item._children,
            diff_dict,
            op_type,
            register_edit=False,
        )
        edit_list = [ordered_dict_edit]
        # TODO: Is there a nicer way to do composite edits than needing this
        # reverse order flag? Eg. is there a way to build these edits so that
        # the order doesn't matter?
        reverse_order_for_inverse = True

        if op_type == OrderedDictOp.RENAME:
            name_change_edit = SelfInverseSimpleEdit(
                tree_item,
                run_func=self._rename,
                register_edit=False,
            )
            edit_list = [name_change_edit, ordered_dict_edit]
            # Name change needs to be done before dict change both times
            reverse_order_for_inverse = False

        elif op_type == OrderedDictOp.REMOVE:
            remove_parent_edit = SelfInverseSimpleEdit(
                tree_item,
                run_func=self._remove,
                register_edit=False,
            )
            # Order is important here: need to remove parent first
            edit_list = [remove_parent_edit, ordered_dict_edit]

        elif op_type in [OrderedDictOp.ADD, OrderedDictOp.INSERT]:
            add_parent_edit = SelfInverseSimpleEdit(
                tree_item,
                run_func=self._add_or_insert,
                register_edit=False,
            )
            # Order is important here: need to add it to dict first
            edit_list = [ordered_dict_edit, add_parent_edit]

        super(BaseTreeEdit, self).__init__(
            edit_list,
            reverse_order_for_inverse=reverse_order_for_inverse,
            register_edit=register_edit,
        )

    def _rename(self, tree_item, inverse):
        """Additional renaming edit for tree name child.

        This changes the child's name attribute. Notice that due to the
        implementation of this, it's important that it's run BEFORE the
        ordered dict rename edit, as otherwise, the child will have the
        new name and won't be found by tree_item.get_child(). The same
        is true of the inverse of this function.

        Args:
            tree_item (BaseTreeItem): tree item whose child we're renaming.
            inverse (bool): flag for if this function is being run as an
                inverse or not.
        """
        for name_tuple in self.diff_dict.items():
            original_name = name_tuple[1] if inverse else name_tuple[0]
            new_name = name_tuple[0] if inverse else name_tuple[1]
            child = tree_item.get_child(original_name)
            if child:
                child._name = new_name

    # TODO: merge this and the method below
    def _remove(self, tree_item, inverse):
        """Additional remove edit for removing tree child.

        This removes/readds the child's parent attribute.

        Args:
            tree_item (BaseTreeItem): tree item whose child we're renaming.
            inverse (bool): flag for if this function is being run as an
                inverse or not.
        """
        for name in self.diff_dict.keys():
            child = tree_item.get_child(name)
            if child:
                if inverse:
                    child._parent = tree_item
                else:
                    child._parent = None

    def _add_or_insert(self, tree_item, inverse):
        """Additional remove edit for adding/inserting tree child.

        This adds/removes the child's parent attribute.

        Args:
            tree_item (BaseTreeItem): tree item whose child we're renaming.
            inverse (bool): flag for if this function is being run as an
                inverse or not.
        """
        for name in self.diff_dict.keys():
            child = tree_item.get_child(name)
            if child:
                if inverse:
                    child._parent = None
                else:
                    child._parent = tree_item


class AddChildrenEdit(BaseTreeEdit):
    """Tree edit for adding children."""

    def __init__(self, tree_item, children_to_add, register_edit=True):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_add (dict(str, BaseTreeItem)): dict of children
                to add, keyed by names. This can be ordered or not, depending
                on whether we care which is added first.
            register_edit (bool): whether or not to register this edit.
        """
        super(AddChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(children_to_add),
            op_type=OrderedDictOp.ADD,
            register_edit=register_edit,
        )

        self._name = "AddChildren ({0})".format(tree_item.name)
        self._description = "Add children to {1}: [{0}]".format(
            ",".join(list(children_to_add.keys())),
            tree_item.path
        )


class InsertChildrenEdit(BaseTreeEdit):
    """Tree edit for adding children."""

    def __init__(self, tree_item, children_to_insert, register_edit=True):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_insert (dict(str, tuple(index, BaseTreeItem))):
                dict representing children to insert and where to insert them.
                This can be ordered or not, depending on whether we care which
                is inserted first.
            register_edit (bool): whether or not to register this edit.
        """
        super(InsertChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(children_to_insert),
            op_type=OrderedDictOp.INSERT,
            register_edit=register_edit,
        )

        self._name = "InsertChildren ({0})".format(tree_item.name)
        self._description = (
            "Insert children to {0}: [{1}]".format(
                tree_item.path,
                ",".join([
                    "(" + key + " --> index " + str(value[0]) + ")"
                    for key, value in children_to_insert.items()
                ])
            )
        )


class RemoveChildrenEdit(BaseTreeEdit):
    """Tree edit for removing children."""

    def __init__(self, tree_item, children_to_remove, register_edit=True):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_remove (list(str)): list of names of children to
                remove.
            register_edit (bool): whether or not to register this edit.
        """
        super(RemoveChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(
                [(name, None) for name in children_to_remove]
            ),
            op_type=OrderedDictOp.REMOVE,
            register_edit=register_edit,
        )

        self._name = "RemoveChildren ({0})".format(tree_item.name)
        self._description = "Remove children from {1}: [{0}]".format(
            ",".join(children_to_remove),
            tree_item.path
        )


class RenameChildrenEdit(BaseTreeEdit):
    """Tree edit for renaming children."""

    def __init__(self, tree_item, children_to_rename, register_edit=True):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_remove (dict(str, str)): dict of old names of children
                and new ones to replace them with. Can be ordered or not.
            register_edit (bool): whether or not to register this edit.
        """
        super(RenameChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(children_to_rename),
            op_type=OrderedDictOp.RENAME,
            register_edit=register_edit,
        )

        self._name = "RenameChildren ({0})".format(tree_item.name)
        self._description = (
            "Rename children of {0}: [{1}]".format(
                tree_item.path,
                ",".join([
                    "(" + key + " --> " + value + ")"
                    for key, value in children_to_rename.items()
                ])
            )
        )    


class ModifyChildrenEdit(BaseTreeEdit):
    """Tree edit for swapping children of given names with new children."""

    def __init__(self, tree_item, children_to_modify, register_edit=True):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_modify (dict(str, BaseTreeItem)): dict of names of
                children and new tree items to replace them with. Can be
                ordered or not.
            register_edit (bool): whether or not to register this edit.
        """
        super(ModifyChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(children_to_modify),
            op_type=OrderedDictOp.MODIFY,
            register_edit=register_edit,
        )

        self._name = "ModifyChildren ({0})".format(tree_item.name)
        self._description = (
            "Modify children of {0}: [{1}]".format(
                tree_item.path,
                ",".join(list(children_to_modify.keys()))
            )
        )


class MoveChildrenEdit(BaseTreeEdit):
    """Tree edit for moving positions of children."""

    def __init__(self, tree_item, children_to_move, register_edit=True):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_move (dict(str, int)): dict of names of children to
                move and new positions to move them to. This can be ordered or
                not, depending on whether we care about which child is moved
                first. Can be ordered or not.
            register_edit (bool): whether or not to register this edit.
        """
        super(MoveChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(children_to_move),
            op_type=OrderedDictOp.MOVE,
            register_edit=register_edit,
        )

        self._name = "MoveChildren ({0})".format(tree_item.name)
        self._description = (
            "Move children of {0}: [{1}]".format(
                tree_item.path,
                ",".join([
                    "(" + key + " --> " + str(value) + ")"
                    for key, value in children_to_move.items()
                ])
            )
        )


class MoveTreeItemEdit(CompositeEdit):
    """Tree edit for moving a tree item under another parent."""

    def __init__(self, tree_item, new_parent, index, register_edit=True):
        """Initialise edit item.

        This edit assumes that it is legal for tree_item to be a child of
        new_parent, ie. that tree_item is in new_parent's allowed_child_types.

        Args:
            tree_item (BaseTreeItem): tree item to move.
            new_parent (BaseTreeItem): new parent to move under.
            index (int): index to add child at.
            register_edit (bool): whether or not to register this edit.
        """
        insert_child_edit = InsertChildrenEdit(
            new_parent,
            {tree_item.name: (index, tree_item)},
            register_edit=False,
        )
        if not tree_item.parent:
            super(MoveTreeItemEdit, self).__init__(
                [insert_child_edit],
                register_edit=register_edit,
            )
        else:
            remove_child_edit = RemoveChildrenEdit(
                tree_item.parent,
                [tree_item.name],
                register_edit=False,
            )
            super(MoveTreeItemEdit, self).__init__(
                [remove_child_edit, insert_child_edit],
                register_edit=register_edit,
            )

        self._name = "MoveTreeItem ({0})".format(tree_item.name)
        self._description = (
            "Move tree item {0} --> {1} (at child index {2})".format(
                tree_item.path,
                tree_item.TREE_PATH_SEPARATOR.join(
                    [new_parent.path, tree_item.name]
                ),
                index
            )
        )
