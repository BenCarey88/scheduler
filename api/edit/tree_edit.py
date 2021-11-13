"""Tree edits to be applied to tree items."""

from collections import OrderedDict

from ._base_edit import BaseDiffEdit, BaseEdit, SelfInverseSimpleEdit
from .composite_edit import CompositeEdit
from .ordered_dict_edit import EditOperation, OrderedDictEdit


class BaseTreeEdit(CompositeEdit):
    """Object representing an edit that can be called on a tree item."""

    def __init__(self, tree_item, diff_dict, op_type, register_edit=True):
        """Initialise base tree edit.

        Args:
            diff_dict (OrderedDict): diff dict 
        """
        ordered_dict_edit = OrderedDictEdit(
            tree_item._children,
            diff_dict,
            op_type,
            register_edit=False
        )
        if op_type == EditOperation.RENAME:
            name_change_edit = SelfInverseSimpleEdit(
                tree_item,
                self._rename,
                register_edit=False
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

    def _rename(self, tree_item):
        """Additional renaming edit for tree name."""
        for name, new_name in self.diff_dict.items():
            child = tree_item._children.get(name)
            if child:
                child._name = new_name

    # def _run(self, tree_items):
    #     """Run this edit on a tree item.

    #     This method just applies an OrderedDictEdit to the tree's child
    #     (this class is a 'friend' of BaseTreeItem, hence why it can access
    #     the 'private' _children and _name variables).

    #     We also add additional logic to the RENAME operation to ensure that
    #     renaming a tree in its parent's child_dict will also alter the child
    #     item's name attribute.

    #     Args:
    #         tree_item (BaseTreeItem): tree item whose child dict is being
    #             edited.
    #     """
    #     super(BaseTreeEdit, self)._run(
    #         ([tree_item._children], {})
    #     )


#     def _run(self, tree_item):
#         """Run this edit on a tree item.

#         This method just applies an OrderedDictEdit to the tree's child
#         (this class is a 'friend' of BaseTreeItem, hence why it can access
#         the 'private' _children and _name variables).

#         We also add additional logic to the RENAME operation to ensure that
#         renaming a tree in its parent's child_dict will also alter the child
#         item's name attribute.

#         Args:
#             tree_item (BaseTreeItem): tree item whose child dict is being
#                 edited.
#         """
#         ordered_dict = tree_item._children
#         if self.operation_type == EditOperation.RENAME:
#             for name, new_name in self.diff_dict.items():
#                 child = ordered_dict.get(name)
#                 if child:
#                     child._name = new_name

#         super(BaseTreeEdit, self)._run(ordered_dict)


class TreeAddChildrenEdit(BaseTreeEdit):
    """Tree edit for adding children."""

    def __init__(self, tree_item, children_to_add, register_edit=True):
        """Initialise edit item.

        Args:
            children_to_add (OrderedDict(str, BaseTreeItem)): dict of children
                to add, keyed by names.
            register_edit (bool): whether or not to register this edit.
        """
        super(TreeAddChildrenEdit, self).__init__(
            diff_dict=children_to_add,
            op_type=EditOperation.ADD,
            register_edit=register_edit,
        )


class TreeRemoveChildrenEdit(BaseTreeEdit):
    """Tree edit for removing children."""

    def __init__(self, children_to_remove, register_edit=True):
        """Initialise edit item.

        Args:
            children_to_remove (OrderedDict(str, None)): list of names of
                children to remove.
            register_edit (bool): whether or not to register this edit.
        """
        super(TreeRemoveChildrenEdit, self).__init__(
            diff_dict=OrderedDict(
                [(name, None) for name in children_to_remove]
            ),
            op_type=EditOperation.REMOVE,
            register_edit=register_edit,
        )

# TODO: getting slightly messy running these on top of eachother
# maybe better to treat the inverse diff dict as part of the base edit and
# then treat each of these as separate BaseEdit derived classes?
# or should we literally have every edit operation is a separate class?
# would mean the as_inverse method needs some work since it can't just use
# the same class any more, but presumably we could pass in the class to it
# too and not make it a class method?
# Also means we can decide on case by case basis which derives from
# OrderedDict edit
# BUUUUT: it means that the current quite nice setup for BaseTreeEdit where
# it inherits from ALL the OrderedDictEdits doesn't work, which is
# annoying.
#
# OR (/and) a nicer structure is to change the base class from:
#           __call__  -->  _run
# to:
#           __call__ --> _run_and_register --> _run
# then can just implement the _run method and not have to worry about the
# annoying super calls
# OH DAMMIT just remembered though that the register NEEDS to be passed the
# same arguments as _run in order to save the _args and _kwargs properly,
# so may end up with the same issue?
class TaskEdit(BaseEdit):
    """Object representing an edit on a task tree item."""

    def _run(self, task_item, *args, **kwargs):
        """Run this edit on a task item.

        The formats of the associated diff dicts are described below.

        Args:
            task_item (TaskItem or None): task tree item whose child dict
                is being edited.

        diff_dict formats:
            CHANGE_TASK_TYPE: {new_type: None} - change task type to new type.
            ADD: {date: dict} - update task history dict to add the new dict
                at the given date. The dict should have a status key and
                optionally a comments key.
        """
        ordered_dict = task_item.history.dict

        if self.operation_type == EditOperation.CHANGE_TASK_TYPE:
            old_task_type = task_item.type
            if self.inverse_diff_dict is None:
                self.inverse_diff_dict = OrderedDict([old_task_type, None])
            task_item.type = self.diff_dict.keys()[0]

        elif self.operation_type == EditOperation.ADD:
            for date, _dict in self.diff_dict.items():
                status = _dict["status"]

        kwargs["ordered_dict"] = ordered_dict
        super(TaskEdit, self)._run(
            *args,
            task_item=task_item,
            **kwargs,
        )


# TODO: Make CompositeEdit class
# probably just use several sub-edits and make sure each is set to register=False
