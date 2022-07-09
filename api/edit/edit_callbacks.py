"""Module for managing edit callbacks."""

from functools import partial

from . import edit_log
from .tree_edit import (
    InsertChildrenEdit,
    MoveChildrenEdit,
    MoveTreeItemEdit,
    RemoveChildrenEdit,
    RenameChildrenEdit,
    ReplaceTreeItemEdit,
)
from .task_edit import (
    ChangeTaskTypeEdit,
    UpdateTaskHistoryEdit,
)
from .planner_edit import (
    AddPlannedItemEdit,
    AddPlannedItemAsChildEdit,
    ModifyPlannedItemEdit,
    MovePlannedItemEdit,
    RemovePlannedItemEdit,
    SortPlannedItemsEdit,
)
from .schedule_edit import (
    AddScheduledItemEdit,
    AddScheduledItemAsChildEdit,
    RemoveScheduledItemEdit,
    ModifyScheduledItemEdit,
    ModifyRepeatScheduledItemEdit,
    ModifyRepeatScheduledItemInstanceEdit,
    ReplaceScheduledItemEdit,
)


class CallbackItemType(object):
    """Struct representing callback item types."""
    TREE = "Tree"
    SCHEDULER = "Scheduler"
    PLANNER = "Planner"


class CallbackEditType(object):
    """Struct representing callback edit types."""
    ADD = "add"
    REMOVE = "remove"
    MODIFY = "modify"
    MOVE = "move"
    FULL_UPDATE = "full_update"

    @classmethod
    def inverse(cls, value):
        """Get inverse callback type.

        Args:
            value (CallbackEditType): the callback type.

        Returns:
            (CallbackEditType): the inverse callback type.
        """
        return {
            cls.ADD: cls.REMOVE,
            cls.REMOVE: cls.ADD,
        }.get(value, value)


class CallbackType(object):
    """Struct to store the different callback types.

    A callback type consists of a combination of an item type (ie. the
    type of thing we're editing) and an edit type (ie. the type of edit).
    The supported callback types, along with their arguments and associated
    edits are as follows:

    Tree:
        TREE_ADD:
            Args:   (tree_item, parent, row)
            Edits:  [InsertChildrenEdit]
        TREE_REMOVE:
            Args:   (tree_item, parent, row)
            Edits:  [RemoveChildrenEdit]
        TREE_MODIFY:
            Args:   (old_tree_item, new_tree_item),
            Edits:  [
                RenameChildrenEdit,
                ReplaceTreeItemEdit,
                ChangeTaskTypeEdit,
                UpdateTaskHistoryEdit,
            ]
        TREE_MOVE:
            Args:   (tree_item, old_parent, old_row, new_parent, new_row)
            Edits:  [MoveChildrenEdit, MoveTreeItemEdit]

    Scheduler:      
        SCHEDULER_ADD:
            Args:   (scheduled_item)
            Edits:  [AddScheduledItemEdit, AddScheduledItemAsChildEdit]
        SCHEDULER_REMOVE:
            Args:   (scheduled_item)
            Edits:  [RemoveScheduledItemEdit]
        SCHEDULER_MODIFY:
            Args:   (old_scheduled_item, new_scheduled_item)
            Edits:  [
                ModifyScheduledItemEdit,
                ModifyRepeatScheduledItemEdit,
                ModifyRepeatScheduledItemInstanceEdit,
                ReplaceScheduledItemEdit,
            ]

    Planner:
        PLANNER_ADD:
            Args:   (planned_item, calendar_period, row)
            Edits:  [AddPlannedItemEdit, AddPlannedItemAsChildEdit]
        PLANNER_REMOVE:
            Args:   (planned_item, calendar_period, row)
            Edits:  [RemovePlannedItemEdit]
        PLANNER_MODIFY:
            Args:   (item, period, row, new_item, new_period, new_row)
            Edits:  [ModifyPlannedItemEdit]
        PLANNER_MOVE:
            Args:   (planned_item, old_period, old_row, new_period, new_row)
            Edits:  [MovePlannedItemEdit]
        PLANNER_FULL_UPDATE:
            Args:   (calendar_period)
            Edits:  [SortPlannedItemsEdit]
    """
    TREE_ADD = (CallbackItemType.TREE, CallbackEditType.ADD)
    TREE_REMOVE = (CallbackItemType.TREE, CallbackEditType.REMOVE)
    TREE_MODIFY = (CallbackItemType.TREE, CallbackEditType.MODIFY)
    TREE_MOVE = (CallbackItemType.TREE, CallbackEditType.MOVE)
    SCHEDULER_ADD = (CallbackItemType.SCHEDULER, CallbackEditType.ADD)
    SCHEDULER_REMOVE = (CallbackItemType.SCHEDULER, CallbackEditType.REMOVE)
    SCHEDULER_MODIFY = (CallbackItemType.SCHEDULER, CallbackEditType.MODIFY)
    PLANNER_ADD = (CallbackItemType.PLANNER, CallbackEditType.ADD)
    PLANNER_REMOVE = (CallbackItemType.PLANNER, CallbackEditType.REMOVE)
    PLANNER_MODIFY = (CallbackItemType.PLANNER, CallbackEditType.MODIFY)
    PLANNER_MOVE = (CallbackItemType.PLANNER, CallbackEditType.MOVE)
    PLANNER_FULL_UPDATE = (
        CallbackItemType.PLANNER, CallbackEditType.FULL_UPDATE
    )

    EDIT_CLASS_MAPPING = {
        TREE_ADD: [InsertChildrenEdit],
        TREE_REMOVE: [RemoveChildrenEdit],
        TREE_MODIFY: [
            RenameChildrenEdit,
            ReplaceTreeItemEdit,
            ChangeTaskTypeEdit,
            UpdateTaskHistoryEdit,
        ],
        TREE_MOVE: [MoveChildrenEdit, MoveTreeItemEdit],
        SCHEDULER_ADD: [AddScheduledItemEdit, AddScheduledItemAsChildEdit],
        SCHEDULER_REMOVE: [RemoveScheduledItemEdit],
        SCHEDULER_MODIFY: [
            ModifyScheduledItemEdit,
            ModifyRepeatScheduledItemEdit,
            ModifyRepeatScheduledItemInstanceEdit,
            ReplaceScheduledItemEdit,
        ],
        PLANNER_ADD: [AddPlannedItemEdit, AddPlannedItemAsChildEdit],
        PLANNER_REMOVE: [RemovePlannedItemEdit],
        PLANNER_MODIFY: [ModifyPlannedItemEdit],
        PLANNER_MOVE: [MovePlannedItemEdit],
        PLANNER_FULL_UPDATE: [SortPlannedItemsEdit],
    }

    @classmethod
    def inverse(cls, value):
        """Get inverse callback type.

        Args:
            value (tuple(CallbackItemType, CallbackEditType)): the
                callback type.

        Returns:
            (tuple(CallbackItemType, CallbackEditType)): the inverse
                callback type.
        """
        return (value[0], CallbackEditType.inverse(value[1]))

    @classmethod
    def get_edit_classes(cls, callback_type):
        """Get edit classes to register for given callback type.

        Args:
            value (tuple(CallbackItemType, CallbackEditType)): the
                callback type.

        Returns:
            (list(class)): the edit classes for that callback type.
        """
        return cls.EDIT_CLASS_MAPPING.get(callback_type, [])

    @classmethod
    def get_inverse_edit_classes(cls, callback_type):
        """Get edit classes to register as undo for given callback type.

        Args:
            value (tuple(CallbackItemType, CallbackEditType)): the
                callback type.

        Returns:
            (list(class)): the inverse edit classes for that callback type.
        """
        return cls.EDIT_CLASS_MAPPING.get(cls.inverse(callback_type), [])


def _modify_callback(callback_type, callback):
    """Modify callback so args can match those defined in the edit.

    This is needed for tree edit callbacks because the edits can be
    applied to multiple items but (currently) the application of them
    in the tree manager class always runs on a single item, so the
    arguments change.

    Args:
        callback_type (CallbackType): callback type.
        callback (function): callback to modify.

    Returns:
        (function): modified callback.
    """
    if callback_type[0] == CallbackItemType.TREE:
        def modified_callback(arg_tuple):
            # Note that this won't work if tree edit is done on multiple items.
            return callback(*arg_tuple)
        return modified_callback
    else:
        return callback


def register_pre_callback(callback_type, id, callback):
    """Register pre-edit and pre-edit-undo callback.

    Args:
        callback_type (CallbackType): callback type to register.
        id (variant): id to register callback at. Generally this will
            be the ui class that defines the callback.
        callback (function): callback to run before an item is added.
            This should accept arguments specified in the run func below.
    """
    callback = _modify_callback(callback_type, callback)
    for edit_class in CallbackType.get_edit_classes(callback_type):
        edit_class.register_pre_edit_callback(id, callback)
    for edit_class in CallbackType.get_inverse_edit_classes(callback_type):
        edit_class.register_pre_undo_callback(id, callback)


def register_post_callback(callback_type, id, callback):
    """Register post-edit and post-edit-undo callback.

    Args:
        callback_type (CallbackType): callback type to register.
        id (variant): id to register callback at. Generally this will
            be the ui class that defines the callback.
        callback (function): callback to run before an item is added.
            This should accept arguments specified in the run func below.
    """
    callback = _modify_callback(callback_type, callback)
    for edit_class in CallbackType.get_edit_classes(callback_type):
        edit_class.register_post_edit_callback(id, callback)
    for edit_class in CallbackType.get_inverse_edit_classes(callback_type):
        edit_class.register_post_undo_callback(id, callback)


def register_general_purpose_pre_callback(id, callback):
    """Register a single function that can handle pre-callbacks for all edits.

    Args:
        id (variant): id to register.
        callback (function): function to process callback. This function
            will need to accept a callback_type arg and an arbitrary number
            of subsequent args that depend on the callback type.
    """
    for callback_type in CallbackType.EDIT_CLASS_MAPPING.keys():
        register_pre_callback(
            callback_type,
            id,
            partial(callback, callback_type),
        )


def register_general_purpose_post_callback(id, callback):
    """Register a single function that can handle post-callbacks for all edits.

    Args:
        id (variant): id to register.
        callback (function): function to process callback. This function
            will need to accept a callback_type arg and an arbitrary number
            of subsequent args that depend on the callback type.
    """
    for callback_type in CallbackType.EDIT_CLASS_MAPPING.keys():
        register_post_callback(
            callback_type,
            id,
            partial(callback, callback_type),
        )


def remove_callbacks(id):
    """Remove all callbacks registered with given id.

    Args:
        id (variant): id to remove callbacks for.
    """
    edit_log.remove_edit_callbacks(id)
