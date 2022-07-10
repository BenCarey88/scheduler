"""Tree edits to be applied to tree items."""

from collections import OrderedDict

from ._core_edits import (
    AttributeEdit,
    CompositeEdit,
    HostedDataEdit,
    RemoveFromHostEdit,
)
from ._container_edit import DictEdit, ContainerOp


class BaseTreeEdit(CompositeEdit):
    """Edit that can be called on a tree item."""

    def __init__(self, tree_item, diff_dict, op_type):
        """Initialise base tree edit.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            diff_dict (OrderedDict): a dictionary representing modifications
                to the tree item's child dict. How to interpret this dictionary
                depends on the operation type.
            operation_type (ContainerOp): The type of edit operation to do.
        """
        ordered_dict_edit = DictEdit.create_unregistered(
            tree_item._children,
            diff_dict,
            op_type,
        )
        edit_list = [ordered_dict_edit]

        if op_type == ContainerOp.RENAME:
            name_change_edit = AttributeEdit.create_unregistered(
                {
                    tree_item.get_child(old_name)._name: new_name
                    for old_name, new_name in diff_dict.items()
                    if tree_item.get_child(old_name)
                },
            )
            edit_list = [name_change_edit, ordered_dict_edit]

        elif op_type == ContainerOp.REMOVE:
            remove_parent_edit = AttributeEdit.create_unregistered({
                tree_item.get_child(name)._parent: None
                for name in diff_dict
                if tree_item.get_child(name)
            })
            # remove_from_host_edit = CompositeEdit.create_unregistered([
            #     RemoveFromHostEdit.create_unregistered(tree_item.get_child(n))
            #     for n in diff_dict
            #     if tree_item.get_child(n)
            # ])
            edit_list = [
                remove_parent_edit,
                ordered_dict_edit,
                # remove_from_host_edit,
            ]

        elif op_type == ContainerOp.ADD:
            add_parent_edit = AttributeEdit.create_unregistered(
                {
                    new_child._parent: tree_item
                    for new_child in diff_dict.values()
                },
            )
            edit_list = [ordered_dict_edit, add_parent_edit]

        elif op_type == ContainerOp.INSERT:
            insert_parent_edit = AttributeEdit.create_unregistered(
                {
                    new_child._parent: tree_item
                    for _, new_child in diff_dict.values()
                },
            )
            edit_list = [ordered_dict_edit, insert_parent_edit]

        elif op_type == ContainerOp.MODIFY:
            modify_parent_edit = AttributeEdit.create_unregistered(
                {
                    new_child._parent: tree_item
                    for name, new_child in diff_dict.values()
                    if tree_item.get_child(name)
                },
            )
            edit_list = [ordered_dict_edit, modify_parent_edit]

        super(BaseTreeEdit, self).__init__(
            edit_list,
            validity_check_edits=[ordered_dict_edit],
        )


class AddChildrenEdit(BaseTreeEdit):
    """Tree edit for adding children."""
    def __init__(self, tree_item, children_to_add):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_add (dict(str, BaseTreeItem)): dict of children
                to add, keyed by names. This can be ordered or not, depending
                on whether we care which is added first.
        """
        super(AddChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(children_to_add),
            op_type=ContainerOp.ADD,
        )

        # TODO: really not sure what the best way to present args here is
        self._callback_args = [
            (child, tree_item, tree_item.num_children() + i)
            for i, child in enumerate(children_to_add.values())
        ]
        self._undo_callback_args = reversed(self._callback_args)

        self._name = "AddChildren ({0})".format(tree_item.name)
        self._description = "Add children to {1}: [{0}]".format(
            ",".join(list(children_to_add.keys())),
            tree_item.path
        )


class InsertChildrenEdit(BaseTreeEdit):
    """Tree edit for adding children."""
    def __init__(self, tree_item, children_to_insert):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_insert (dict(str, tuple(index, BaseTreeItem))):
                dict representing children to insert and where to insert them.
                This can be ordered or not, depending on whether we care which
                is inserted first.
        """
        super(InsertChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(children_to_insert),
            op_type=ContainerOp.INSERT,
        )

        self._callback_args = [
            (child, tree_item, row)
            for row, child in children_to_insert.values()
        ]
        self._undo_callback_args = list(reversed(self._callback_args))

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
    def __init__(self, tree_item, children_to_remove):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_remove (list(str)): list of names of children to
                remove.
        """
        super(RemoveChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(
                [(name, None) for name in children_to_remove]
            ),
            op_type=ContainerOp.REMOVE,
        )

        self._callback_args = [
            (tree_item.get_child(n), tree_item, tree_item.get_child(n).index())
            for n in children_to_remove
            if tree_item.get_child(n) is not None
            and tree_item.get_child(n).index() is not None
        ]
        self._undo_callback_args = list(reversed(self._callback_args))

        self._name = "RemoveChildren ({0})".format(tree_item.name)
        self._description = "Remove children from {1}: [{0}]".format(
            ",".join(children_to_remove),
            tree_item.path
        )


class RenameChildrenEdit(BaseTreeEdit):
    """Tree edit for renaming children."""
    def __init__(self, tree_item, children_to_rename):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_remove (dict(str, str)): dict of old names of children
                and new ones to replace them with. Can be ordered or not.
        """
        super(RenameChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(children_to_rename),
            op_type=ContainerOp.RENAME,
        )

        self._callback_args = self._undo_callback_args = ([
            (tree_item.get_child(old_name), tree_item.get_child(old_name))
            for (old_name, _) in children_to_rename.items()
            if tree_item.get_child(old_name) is not None
        ])

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
    def __init__(self, tree_item, children_to_modify):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_modify (dict(str, BaseTreeItem)): dict of names of
                children and new tree items to replace them with. Can be
                ordered or not.
        """
        super(ModifyChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(children_to_modify),
            op_type=ContainerOp.MODIFY,
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
    def __init__(self, tree_item, children_to_move):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_move (dict(str, int)): dict of names of children to
                move and new positions to move them to. This can be ordered or
                not, depending on whether we care about which child is moved
                first. Can be ordered or not.
        """
        super(MoveChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(children_to_move),
            op_type=ContainerOp.MOVE,
        )

        self._callback_args = [
            (
                tree_item.get_child(name),
                tree_item,
                tree_item.get_child(name).index(),
                tree_item,
                index,
            )
            for name, index in children_to_move.items()
            if tree_item.get_child(name) is not None
            and tree_item.get_child(name).index() is not None
        ]
        self._undo_callback_args = [
            (
                tree_item.get_child(name),
                tree_item,
                index,
                tree_item,
                tree_item.get_child(name).index(),
            )
            for name, index in reversed(children_to_move.items())
            if tree_item.get_child(name) is not None
            and tree_item.get_child(name).index() is not None
        ]

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
    def __init__(self, tree_item, new_parent, index=None):
        """Initialise edit item.

        This edit assumes that it is legal for tree_item to be a child of
        new_parent, ie. that tree_item is in new_parent's allowed_child_types.

        Args:
            tree_item (BaseTreeItem): tree item to move.
            new_parent (BaseTreeItem): new parent to move under.
            index (int or None): index to add child at. If None, add at end.
        """
        if new_parent == tree_item.parent and index == tree_item.index():
            super(MoveTreeItemEdit, self).__init__([])
            self._is_valid = False
            return

        if index is not None:
            insert_child_edit = InsertChildrenEdit.create_unregistered(
                new_parent,
                {tree_item.name: (index, tree_item)},
            )
        else:
            insert_child_edit = AddChildrenEdit.create_unregistered(
                new_parent,
                {tree_item.name: tree_item},
            )

        if not tree_item.parent:
            super(MoveTreeItemEdit, self).__init__(
                [insert_child_edit],
            )
        else:
            remove_child_edit = RemoveChildrenEdit.create_unregistered(
                tree_item.parent,
                [tree_item.name],
            )
            super(MoveTreeItemEdit, self).__init__(
                [remove_child_edit, insert_child_edit],
            )

        self._callback_args = [(
            tree_item,
            tree_item.parent,
            tree_item.index(),
            new_parent,
            index if index is not None else new_parent.num_children(),
        )]
        self._undo_callback_args = [(
            tree_item,
            new_parent,
            index if index is not None else new_parent.num_children(),
            tree_item.parent,
            tree_item.index(),
        )]

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


class ReplaceTreeItemEdit(CompositeEdit):
    """Replace one tree item with another."""
    def __init__(self, old_tree_item, new_tree_item):
        """Initialise edit.

        This edit assumes that it is legal for tree_item to be a child of
        new_parent, ie. that tree_item is in new_parent's allowed_child_types.

        Note that this edit also passes all of old_tree_item's children over to
        new_tree_item. The intended use is on a new_tree_item that has just
        been made and doesn't have any children of its own.

        Args:
            old_tree_item (BaseTreeItem): tree item to replace.
            new_tree_item (BaseTreeItem): tree item to replace it with.
        """
        if old_tree_item.parent is None or old_tree_item == new_tree_item:
            super(ReplaceTreeItemEdit, self).__init__([])
            self._is_valid = False
            return

        remove_edit = RemoveChildrenEdit.create_unregistered(
            old_tree_item.parent,
            [old_tree_item.name],
        )
        add_edit = MoveTreeItemEdit.create_unregistered(
            new_tree_item,
            old_tree_item.parent,
            old_tree_item.index(),
        )
        switch_host_edit = HostedDataEdit.create_unregistered(
            old_tree_item,
            new_tree_item,
        )
        subedits = [remove_edit, add_edit, switch_host_edit]
        for child in old_tree_item._children.values():
            subedits.append(
                MoveTreeItemEdit.create_unregistered(child, new_tree_item)
            )
        super(ReplaceTreeItemEdit, self).__init__(subedits)

        self._callback_args = [(old_tree_item, new_tree_item)]
        self._undo_callback_args = [(new_tree_item, old_tree_item)]

        self._name = "ReplaceTreeItem ({0})".format(old_tree_item.name)
        self._description = "Replace tree item {0} --> {1}".format(
            old_tree_item.path,
            new_tree_item.path,
        )
