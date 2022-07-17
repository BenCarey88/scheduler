"""Tree edits to be applied to tree items."""

from collections import OrderedDict

from ._base_edit import EditError
from ._core_edits import (
    ActivateHostedDataEdit,
    AttributeEdit,
    DeactivateHostedDataEdit,
    CompositeEdit,
    RedirectHostEdit,
    ReplaceHostedDataEdit,
)
from ._container_edit import DictEdit, ContainerOp


class BaseTreeEdit(CompositeEdit):
    """Edit that can be called on a tree item."""

    def __init__(self, tree_item, diff_dict, op_type, include_host_edit=True):
        """Initialise base tree edit.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            diff_dict (OrderedDict): a dictionary representing modifications
                to the tree item's child dict. How to interpret this dictionary
                depends on the operation type.
            operation_type (ContainerOp): The type of edit operation to do.
            include_host_edit (bool): if True, activate/deactivate the item
                during add/remove edits.
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
            edit_list = [remove_parent_edit, ordered_dict_edit]
            if include_host_edit:
                deactivate_subedit = CompositeEdit.create_unregistered([
                    DeactivateHostedDataEdit.create_unregistered(
                        tree_item.get_child(name)
                    )
                    for name in diff_dict
                    if tree_item.get_child(name)
                ])
                edit_list.append(deactivate_subedit)

        elif op_type == ContainerOp.ADD:
            add_parent_edit = AttributeEdit.create_unregistered(
                {
                    new_child._parent: tree_item
                    for new_child in diff_dict.values()
                },
            )
            edit_list = [ordered_dict_edit, add_parent_edit]
            if include_host_edit:
                activate_subedit = CompositeEdit.create_unregistered([
                    ActivateHostedDataEdit.create_unregistered(new_child)
                    for new_child in diff_dict.values()
                ])
                edit_list.insert(0, activate_subedit)

        elif op_type == ContainerOp.INSERT:
            insert_parent_edit = AttributeEdit.create_unregistered(
                {
                    new_child._parent: tree_item
                    for _, new_child in diff_dict.values()
                },
            )
            edit_list = [ordered_dict_edit, insert_parent_edit]
            if include_host_edit:
                activate_subedit = CompositeEdit.create_unregistered([
                    ActivateHostedDataEdit.create_unregistered(new_child)
                    for _, new_child in diff_dict.values()
                ])
                edit_list.insert(0, activate_subedit)

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
    def __init__(self, tree_item, children_to_add, activate=True):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_add (dict(str, BaseTreeItem)): dict of children
                to add, keyed by names. This can be ordered or not, depending
                on whether we care which is added first.
            activate (bool): if True, activate hosted data as part of edit.
        """
        super(AddChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(children_to_add),
            op_type=ContainerOp.ADD,
            include_host_edit=activate,
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
    def __init__(self, tree_item, children_to_insert, activate=True):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_insert (dict(str, tuple(index, BaseTreeItem))):
                dict representing children to insert and where to insert them.
                This can be ordered or not, depending on whether we care which
                is inserted first.
            activate (bool): if True, activate hosted data as part of edit.
        """
        super(InsertChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(children_to_insert),
            op_type=ContainerOp.INSERT,
            include_host_edit=activate,
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
    def __init__(self, tree_item, children_to_remove, deactivate=True):
        """Initialise edit item.

        Args:
            tree_item (BaseTreeItem): the tree item this edit is being run on.
            children_to_remove (list(str)): list of names of children to
                remove.
            deactivate (bool): if True, deactivate as part of edit.
        """
        super(RemoveChildrenEdit, self).__init__(
            tree_item=tree_item,
            diff_dict=OrderedDict(
                [(name, None) for name in children_to_remove]
            ),
            op_type=ContainerOp.REMOVE,
            include_host_edit=deactivate,
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
                activate=False,
            )
        else:
            insert_child_edit = AddChildrenEdit.create_unregistered(
                new_parent,
                {tree_item.name: tree_item},
                activate=False,
            )

        if not tree_item.parent:
            super(MoveTreeItemEdit, self).__init__(
                [insert_child_edit],
            )
        else:
            remove_child_edit = RemoveChildrenEdit.create_unregistered(
                tree_item.parent,
                [tree_item.name],
                deactivate=False,
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
            deactivate=False,
        )
        switch_host_edit = ReplaceHostedDataEdit.create_unregistered(
            old_tree_item,
            new_tree_item,
        )
        add_edit = MoveTreeItemEdit.create_unregistered(
            new_tree_item,
            old_tree_item.parent,
            old_tree_item.index(),
            activate=False,
        )
        subedits = [remove_edit, switch_host_edit, add_edit]
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


class MergeTreeItemsEdit(CompositeEdit):
    """Merge one tree item into another."""
    def __init__(self, src_item, dest_item, override=False, recursive=True):
        """Initialize edit.

        Args:
            src_item (BaseTreeItem): item to merge.
            dest_item (BaseTreeItem): item to merge into.
            override (bool): if True, keep attributes of the source item,
                otherwise keep those of the dest item.
            recursive (bool): if True, run merges for any children with the
                same name. Otherwise just use the child from the source item
                if override is on and the dest item otherwise.
        """
        if not src_item.parent or not dest_item.parent:
            super(MergeTreeItemsEdit, self).__init__([])
            self._is_valid = False
            return
        # remove src item from parent dict
        remove_src_item_edit = RemoveChildrenEdit.create_unregistered(
            src_item.parent,
            [src_item.name],
            deactivate=False,
        )
        subedits = [remove_src_item_edit]
        under_item = src_item
        over_item = dest_item
        if override:
            # Replace dest item with src item
            remove_dest_item_edit = RemoveChildrenEdit.create_unregistered(
                dest_item.parent,
                [dest_item.name],
                deactivate=False,
            )
            rename_src_item_edit = AttributeEdit.create_unregistered(
                {src_item._name: dest_item.name}
            )
            add_src_item_edit = AddChildrenEdit.create_unregistered(
                dest_item.parent,
                {dest_item.name: src_item},
                activate=False,
            )
            subedits.extend([
                remove_dest_item_edit, rename_src_item_edit, add_src_item_edit
            ])
            over_item = src_item
            under_item = dest_item
        # Transfer children
        transfer_children_edits = []
        add_children_dict = {}
        for name, under_child in under_item._children.items():
            over_child = over_item.get_child(name)
            if over_child is not None:
                if recursive:
                    child_merge_edit = MergeTreeItemsEdit.create_unregistered(
                        under_child,
                        over_child,
                        override=False,
                        recursive=True,
                    )
                    transfer_children_edits.append(child_merge_edit)
                else:
                    continue
            else:
                add_children_dict[name] = under_child
        transfer_children_edits.append(
            AddChildrenEdit.create_unregistered(
                over_item,
                add_children_dict,
                activate=False,
            )
        )
        # Redirect host
        redirect_host_edit = RedirectHostEdit.create_unregistered(
            under_item,
            over_item,
        )
        subedits.extend([*transfer_children_edits, redirect_host_edit])
        super(MergeTreeItemsEdit, self).__init__(subedits)


class ArchiveTreeItemEdit(CompositeEdit):
    """Archive a tree item."""
    def __init__(
            self,
            tree_item,
            archive_root,
            rename="",
            merge=True,
            override=True,
            recursive=True):
        """Initialize edit.

        Args:
            tree_item (BaseTreeItem): item to archive.
            archive_root (BaseTreeItem): root of archive tree.
            rename (str): if given, rename the item to this if it already
                exists in the archive. This cannot be given if merge is True.
            merge (bool): if True, and item already exists in archive tree,
                merge this one into it. Otherwise, we rename the item we're
                archiving. This cannot be True if rename arg is given.
            override (bool): if True, keep attributes of the source item when
                merging, otherwise keep those of the dest item. If renaming,
                override=True tells us that the original archived item should
                be renamed rather than the newly archived item.
            recursive (bool): if True, run any merges recursively for children
                of the item that already exist in the archive tree.
        """
        if rename and merge:
            raise EditError(
                "ArchiveTreeItemEdit cannot accept both rename and merge args."
            )
        subedits = []
        archived_item = archive_root.get_item_at_path(tree_item.path)
        if tree_item.parent is None:
            pass

        elif archived_item is None:
            # If item not in archive, add it and any missing ancestors
            remove_edit = RemoveChildrenEdit.create_unregistered(
                tree_item.parent,
                [tree_item.name],
                deactivate=False,
            )
            subedits = [remove_edit]
            closest_ancestor = archive_root.get_shared_ancestor(tree_item)
            if closest_ancestor.path != tree_item.parent.path:
                new_ancestors = archive_root.create_missing_ancestors(
                    tree_item,
                )
                add_ancestors_edit = AddChildrenEdit.create_unregistered(
                    closest_ancestor,
                    {new_ancestors[0].name: new_ancestors[0]},
                    activate=True,
                )
                add_edit = AddChildrenEdit.create_unregistered(
                    new_ancestors[-1],
                    {tree_item.name: tree_item},
                    activate=False,
                )
                subedits.extend([add_ancestors_edit, add_edit])
            else:
                add_edit = AddChildrenEdit.create_unregistered(
                    closest_ancestor,
                    {tree_item.name: tree_item},
                    activate=False,
                )
                subedits.append(add_edit)

        # If item in archive, merge it in or rename it and then add it
        elif merge:
            merge_edit = MergeTreeItemsEdit.create_unregistered(
                tree_item,
                archived_item,
                override=override,
                recursive=recursive,
            )
            # Ignore the remove edit in this case as merge edit covers it
            subedits = [merge_edit]

        elif rename:
            if archived_item.parent.get_child(rename):
                # Can't rename to another name that's also in archive
                super(ArchiveTreeItemEdit, self).__init__([])
                self._is_valid = False
                return
            item_to_rename = tree_item
            tree_item_name = rename
            if override:
                item_to_rename = archived_item
                tree_item_name = tree_item.name

            rename_edit = RenameChildrenEdit.create_unregistered(
                item_to_rename.parent,
                {tree_item.name: rename},
            )
            remove_edit = RemoveChildrenEdit.create_unregistered(
                tree_item.parent,
                [tree_item_name],
                deactivate=False,
            )
            add_edit = AddChildrenEdit(
                archived_item.parent,
                {tree_item_name: tree_item},
                activate=False,
            )
            subedits = [rename_edit, remove_edit, add_edit]

        super(ArchiveTreeItemEdit, self).__init__(subedits)
        self._callback_args = self._undo_callback_args = [
            (tree_item, tree_item.parent, tree_item.index())
        ]
        self._name = "ArchiveTreeItem ({0})".format(tree_item.name)
        self._description = "Archive tree item {0}".format(tree_item.name)


class UnarchiveTreeItemEdit(ArchiveTreeItemEdit):
    """Unarchive a tree item."""
    def __init__(
            self,
            archived_item,
            tree_root,
            rename="",
            merge=True,
            override=True,
            recursive=True):
        """Initialize edit.

        Args:
            archived_item (BaseTreeItem): item to unarchive.
            tree_root (BaseTreeItem): root of main tree.
            rename (str): if given, rename the item to this if it already
                exists in the tree. This cannot be given if merge is True.
            merge (bool): if True, and item already exists in main tree,
                merge this one into it. Otherwise, we rename the item we're
                archiving. This cannot be True if rename arg is given.
            override (bool): if True, keep attributes of the source item when
                merging, otherwise keep those of the dest item. If renaming,
                override=True tells us that the original archived item should
                be renamed rather than the newly archived item.
            recursive (bool): if True, run any merges recursively for children
                of the item that already exist in the archive tree.
        """
        super(UnarchiveTreeItemEdit, self).__init__(
            self,
            archived_item,
            tree_root,
            rename=rename,
            merge=merge,
            override=override,
            recursive=recursive,
        )
        self._name = "UnarchiveTreeItemEdit ({0})".format(archived_item.name)
        self._description = "Unarchive tree item {0}".format(
            archived_item.name
        )
