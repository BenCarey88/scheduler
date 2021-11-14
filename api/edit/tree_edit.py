"""Tree edits to be applied to tree items."""

from collections import OrderedDict

from ._base_edit import SelfInverseSimpleEdit
from ._composite_edit import CompositeEdit
from ._ordered_dict_edit import OrderedDictOp, OrderedDictEdit


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
        ordered_dict_edit = OrderedDictEdit(
            tree_item._children,
            diff_dict,
            op_type,
            register_edit=False,
        )
        if op_type == OrderedDictOp.RENAME:
            name_change_edit = SelfInverseSimpleEdit(
                tree_item,
                run_func=self._rename,
                register_edit=False,
            )
            super(BaseTreeEdit, self).__init__(
                [tree_item, tree_item._children]
                [name_change_edit, ordered_dict_edit],
                register_edit=register_edit,
            )
        else:
            super(BaseTreeEdit, self).__init__(
                [tree_item._children]
                [ordered_dict_edit],
                register_edit=register_edit,
            )

    def _rename(self, tree_item, inverse):
        """Additional renaming edit for tree name child.

        Args:
            tree_item (BaseTreeItem): tree item whose child we're renaming.
            inverse (bool): flag for if this function is being run as an
                inverse or not.
        """
        for name_tuple in self.diff_dict.items():
            original_name = name_tuple[1] if inverse else name_tuple[0]
            new_name = name_tuple[0] if inverse else name_tuple[1]
            child = tree_item._children.get(original_name)
            if child:
                child._name = new_name


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
                    "(" + key + " --> " + value[0] + ")"
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
                and new ones to replace them with.
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
                children and new tree items to replace them with.
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
                first.
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
                    "(" + key + " --> " + value[0] + ")"
                    for key, value in children_to_move.items()
                ])
            )
        )
