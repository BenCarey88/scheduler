# """Callbacks to be used by tree manager class."""

# from scheduler.api.edit.tree_edit import (
#     InsertChildrenEdit,
#     MoveChildrenEdit,
#     MoveTreeItemEdit,
#     RemoveChildrenEdit,
#     RenameChildrenEdit,
#     ReplaceTreeItemEdit,
# )
# from scheduler.api.edit.task_edit import (
#     ChangeTaskTypeEdit,
#     UpdateTaskHistoryEdit,
# )

# from .. _base_callbacks import BaseCallbacks


# # TODO: Note that in fact the edit classes take in a list of these tuples
# # as callback args. Need to decide if we'll ever want to edit multiple items
# # at once and how to deal with that.
# class TreeCallbacks(BaseCallbacks):
#     """Class to manage tree callbacks."""
#     def __init__(self):
#         """Initialize.

#         Callback args:
#             add_edits: (tree_item, parent_item, row)
#             remove_edits: (tree_item, parent_item, row)
#             update_edits: (old_item, new_item)
#             move_edits: (tree_item, old_parent, old_row, new_parent, new_row)
#         """
#         super(TreeCallbacks, self).__init__(
#             add_item_edit_classes=(
#                 InsertChildrenEdit,
#             ),
#             remove_item_edit_classes=(
#                 RemoveChildrenEdit,
#             ),
#             update_item_edit_classes=(
#                 RenameChildrenEdit,
#                 ReplaceTreeItemEdit,
#                 ChangeTaskTypeEdit,
#                 UpdateTaskHistoryEdit,
#             ),
#             move_item_edit_classes=(
#                 MoveChildrenEdit,
#                 MoveTreeItemEdit,
#             ),
#         )

#     def _modify_callback(self, callback):
#         """Modify callback before registering it.

#         This is used to make callback args match the ones defined in
#         the edit class.

#         Args:
#             callback (function): callback to modify.

#         Returns:
#             (function): modified callback.
#         """
#         def modified_callback(arg_tuple):
#             # Note that this won't work with any edit done on multiple items.
#             return callback(*arg_tuple)
#         return modified_callback


# TREE_CALLBACKS = TreeCallbacks()
