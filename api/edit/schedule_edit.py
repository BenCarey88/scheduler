"""Calendar edits to be applied to scheduled items.

Friend classes: [Calendar, CalendarPeriod, ScheduledItem]
"""

from scheduler.api.common.date_time import DateTime
from scheduler.api.utils import fallback_value

from ._container_edit import ListEdit, ContainerOp, ContainerEditFlag
from ._core_edits import (
    ActivateHostedDataEdit,
    AttributeEdit,
    DeactivateHostedDataEdit,
    CompositeEdit,
    ReplaceHostedDataEdit,
    SelfInverseSimpleEdit,
)
from .planner_edit import AddScheduledItemChildRelationshipEdit
from .task_edit import UpdateTaskHistoryEdit


def _get_task_status_update_edits(
        old_scheduled_item,
        new_scheduled_item=None,
        remove_scheduled_item=False,
        new_tree_item=None,
        new_type=None,
        new_date=None,
        new_end_time=None,
        new_update_policy=None,
        new_status=None):
    """Get edits to update the status of the scheduled item's linked task.

    Args:
        old_scheduled_item (BaseScheduledItem): scheduled item we're editing.
        new_scheduled_item (BaseScheduledItem or None): scheduled item after
            editing. If None, use old scheduled item.
        remove_scheduled_item (bool): if True, this edit is removing the
            scheduled item.
        new_tree_item (BaseTaskItem or None): the tree item of the scheduled
            item after editing, if being edited.
        new_date (Date or None): the date of the scheduled item after editing,
            if being edited.
        new_end_time (Time or None): the end time of the scheduled item after
            editing, if being edited.
        new_update_policy (ItemUpdatePolicy or None): the update policy of the
            scheduled item after editing, if being edited.
        new_status (ItemStatus or None): the status of the scheduled item after
            editing, if being edited.

    Returns:
        (list(BaseEdit)): list of edits to update the histories of the linked
            tasks in accordance with the updates to the scheduled items.
    """
    edits = []
    new_scheduled_item = fallback_value(new_scheduled_item, old_scheduled_item)
    old_task = old_scheduled_item._get_task_to_update()
    new_task = new_scheduled_item._get_task_to_update(
        new_type=new_type,
        new_tree_item=new_tree_item,
    )
    if old_task is not None or new_task is not None:
        old_end_datetime = old_scheduled_item.end_datetime
        old_task_status = None
        if old_task is not None:
            old_task_status = old_task.history.get_influenced_status(
                old_end_datetime,
                old_scheduled_item,
            )
        # case 1: remove task history at old date time
        if remove_scheduled_item and old_task_status is not None:
            task_edit = UpdateTaskHistoryEdit.create_unregistered(
                old_task,
                influencer=old_scheduled_item,
                old_datetime=old_end_datetime,
            )
            return [task_edit]

        new_update_policy = fallback_value(
            new_update_policy,
            new_scheduled_item.update_policy,
        )
        new_status = fallback_value(new_status, new_scheduled_item.status)
        new_end_datetime = DateTime.from_date_and_time(
            fallback_value(new_date, new_scheduled_item.date),
            fallback_value(new_end_time, new_scheduled_item.end_time)
        )
        new_task_status = new_update_policy.get_new_status(new_status)

        # case 2: remove from old task history and add to new task history
        if old_task != new_task:
            if old_task_status is not None:
                remove_edit = UpdateTaskHistoryEdit.create_unregistered(
                    old_task,
                    influencer=old_scheduled_item,
                    old_datetime=old_end_datetime,
                )
                edits.append(remove_edit)
            if new_task_status is not None:
                add_edit = UpdateTaskHistoryEdit.create_unregistered(
                    new_task,
                    influencer=new_scheduled_item,
                    new_datetime=new_end_datetime,
                    new_status=new_task_status,
                )
                edits.append(add_edit)
            return edits

        # case 3: update current task history
        elif (new_task_status != old_task_status or
                (new_task_status is not None and
                    old_end_datetime != new_end_datetime)):
            remove = True if new_task_status is None else False
            # note that since task histories use HostedDataDicts, it doesn't
            # matter whether we use old or new scheduled item for the update
            task_edit = UpdateTaskHistoryEdit.create_unregistered(
                old_task,
                influencer=old_scheduled_item,
                old_datetime=old_end_datetime,
                new_datetime=new_end_datetime,
                new_status=new_task_status,
                remove_status=remove,
            )
            edits.append(task_edit)

    return edits


class AddScheduledItemEdit(CompositeEdit):
    """Add scheduled item to calendar."""
    def __init__(self, scheduled_item, activate=True):
        """Initialise edit.

        Args:
            scheduled_item (BaseScheduledItem): the scheduled item to add. Can
                be a single scheduled item instance or a repeating item.
            activate (bool): if True, activate hosted data as part of edit.
        """
        subedits = []
        if activate:
            subedits.append(
                ActivateHostedDataEdit.create_unregistered(scheduled_item)
            )
        add_edit = ListEdit.create_unregistered(
            scheduled_item.get_item_container(),
            [scheduled_item],
            ContainerOp.ADD,
        )
        subedits.append(add_edit)
        super(AddScheduledItemEdit, self).__init__(subedits)
        self._callback_args = self._undo_callback_args = [scheduled_item]
        self._name = "AddScheduledItem ({0})".format(scheduled_item.name)
        self._description = (
            "Add {0} {1} at {2}".format(
                scheduled_item.__class__.__name__,
                scheduled_item.name,
                scheduled_item.datetime_string(),
            )
        )


# TODO: couldn't we just add a parent arg to the AddScheduledItem edit?
# and similar for the planned item ones
class AddScheduledItemAsChildEdit(CompositeEdit):
    """Add scheduled item and make it a child of the given planned item."""
    def __init__(self, scheduled_item, planned_item, index=None):
        """Initialise edit.

        Args:
            scheduled_item (BaseScheduledItem): the scheduled item to add.
            planned_item (PlannedItem): the planned item to set as its parent.
        """
        child_edit = AddScheduledItemChildRelationshipEdit.create_unregistered(
            scheduled_item,
            planned_item,
        )
        if not child_edit._is_valid:
            super(AddScheduledItemAsChildEdit, self).__init__([])
            self._is_valid = False
            return
        add_edit = AddScheduledItemEdit.create_unregistered(scheduled_item)
        super(AddScheduledItemAsChildEdit, self).__init__(
            [add_edit, child_edit]
        )
        self._callback_args = self._undo_callback_args = [scheduled_item]
        self._name = "AddScheduledItemAsChildEdit ({0})".format(
            planned_item.name
        )
        self._description = (
            "Add {0} {1} at {2} and make it a child of {2} {3}".format(
                scheduled_item.__class__.__name__,
                scheduled_item.name,
                scheduled_item.datetime_string(),
                planned_item.__class__.__name__,
                planned_item.name,
            )
        )


class RemoveScheduledItemEdit(CompositeEdit):
    """Remove scheduled item from calendar."""
    def __init__(self, scheduled_item, deactivate=True):
        """Initialise edit.

        Args:
            scheduled_item (BaseScheduledItem): scheduled item to remove. Can be
                a single item or a repeat template.
            deactivate (bool): if True, deactivate hosted data as part of edit.
        """
        remove_edit = ListEdit.create_unregistered(
            scheduled_item.get_item_container(),
            [scheduled_item],
            ContainerOp.REMOVE,
            edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
        )
        subedits = [remove_edit]
        task_edits = _get_task_status_update_edits(
            scheduled_item,
            remove_scheduled_item=True,
        )
        subedits.extend(task_edits)
        if deactivate:
            subedits.append(
                DeactivateHostedDataEdit.create_unregistered(scheduled_item)
            )
        super(RemoveScheduledItemEdit, self).__init__(subedits)
        self._callback_args = self._undo_callback_args = [scheduled_item]
        self._name = "RemoveScheduledItem ({0})".format(scheduled_item.name)
        self._description = (
            "Remove {0} {1} at {2}".format(
                scheduled_item.__class__.__name__,
                scheduled_item.name,
                scheduled_item.datetime_string(),
            )
        )


class BaseModifyScheduledItemEdit(CompositeEdit):
    """Modify attributes (including date and time) of scheduled item.

    This edit should not be called directly, instead there are subclasses
    for each different type of scheduled item: standard, repeat and repeat
    instance.
    """
    def __init__(
            self,
            scheduled_item,
            attr_dict,
            subedits=None,
            keep_last_for_inverse=None):
        """Initialise edit.

        Args:
            scheduled_item (BaseScheduledItem): scheduled item to edit.
            attr_dict (dict(MutableAttribute, variant)): attributes to change.
            subedits (list(BaseEdit) or None): additional edits that subclasses
                may need for dealing with specific attribute changes.
            keep_last_for_inverse (list(BaseEdit) or None): list of edits to
                keep last during inverse, if needed.
        """
        # updateable_attrs = [
        #     scheduled_item._start_time,
        #     scheduled_item._end_time,
        #     scheduled_item._date,
        # ]
        # TODO: ^ I think this bit may be left over from continuous edit
        # paradigm, so can probably be removed?
        self._scheduled_item = scheduled_item
        self._attr_dict = attr_dict
        self._original_attrs = {}
        for attr in list(attr_dict.keys()): # + updateable_attrs:
            # note we need to record updateable attrs here for update to work
            self._original_attrs[attr] = attr.value

        self._attribute_edit = AttributeEdit.create_unregistered(attr_dict)
        subedits = subedits or []
        subedits.insert(0, self._attribute_edit)

        # task history update
        task_history_edits = _get_task_status_update_edits(
            scheduled_item,
            new_tree_item=attr_dict.get(scheduled_item._tree_item),
            new_type=attr_dict.get(scheduled_item._type),
            new_date=attr_dict.get(scheduled_item._date),
            new_end_time=attr_dict.get(scheduled_item._end_time),
            new_update_policy=attr_dict.get(scheduled_item._update_policy),
            new_status=attr_dict.get(scheduled_item._status),
        )
        subedits[1:1] = task_history_edits

        super(BaseModifyScheduledItemEdit, self).__init__(
            subedits,
            keep_last_for_inverse=keep_last_for_inverse,
        )
        self._callback_args = self._undo_callback_args = [
            scheduled_item,
            scheduled_item,
        ]
        self._is_valid = bool(self._modified_attrs())
        self._name = "ModifyScheduledItem ({0})".format(scheduled_item.name)

    def _modified_attrs(self):
        """Get set of all attributes that are modified by edit.

        Returns:
            (set(MutableAttribute)): set of modified attributes.
        """
        return set([
            attr for attr, value in self._attr_dict.items()
            if self._original_attrs.get(attr) != value
        ])

    # TODO: no need to keep this a property now, since continuous edit
    # updates are no longer a thing
    @property
    def description(self):
        """Get description of item.

        Implemented as property so it stays updated.

        Returns:
            (str): description.
        """
        return self._attribute_edit.get_description(
            self._scheduled_item,
            self._scheduled_item.name
        )


class ModifyScheduledItemEdit(BaseModifyScheduledItemEdit):
    """Modify attributes and start and end datetimes of scheduled item."""
    def __init__(self, scheduled_item, attr_dict):
        """Initialise edit.

        Args:
            scheduled_item (ScheduledItem): scheduled item to modify.
            attr_dict (dict(MutableAttribute, variant)): attributes to change.
        """
        subedits = []
        self._remove_edit = None
        self._add_edit = None
        if scheduled_item._date in attr_dict:
            new_date = attr_dict[scheduled_item._date]
            # remove items from old container and add to new one
            self._remove_edit = ListEdit.create_unregistered(
                scheduled_item.get_item_container(),
                [scheduled_item],
                ContainerOp.REMOVE,
                edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
            )
            self._add_edit = ListEdit.create_unregistered(
                scheduled_item.get_item_container(new_date),
                [scheduled_item],
                ContainerOp.ADD,
            )
            subedits.extend([self._remove_edit, self._add_edit])

        super(ModifyScheduledItemEdit, self).__init__(
            scheduled_item,
            attr_dict,
            subedits=subedits,
        )


class ModifyRepeatScheduledItemEdit(BaseModifyScheduledItemEdit):
    """Modify attributes of repeat scheduled item."""
    def __init__(self, scheduled_item, attr_dict):
        """Initialise edit.

        Args:
            scheduled_item (RepeatScheduledItem): scheduled item to modify.
            attr_dict (dict(MutableAttribute, variant)): attributes to change.
        """
        subedits = []
        keep_last_for_inverse = []
        if scheduled_item._repeat_pattern in attr_dict:
            clear_instances = SelfInverseSimpleEdit.create_unregistered(
                scheduled_item._clear_instances,
            )
            subedits.append(clear_instances)
            keep_last_for_inverse.append(clear_instances)
        if (scheduled_item._start_time in attr_dict
                or scheduled_item._end_time in attr_dict):
            clean_overrides = SelfInverseSimpleEdit.create_unregistered(
                scheduled_item._clean_overrides,
            )
            subedits.append(clean_overrides)
            keep_last_for_inverse.append(clean_overrides)
        super(ModifyRepeatScheduledItemEdit, self).__init__(
            scheduled_item,
            attr_dict,
            subedits=subedits,
            keep_last_for_inverse=keep_last_for_inverse,
        )


class ModifyRepeatScheduledItemInstanceEdit(BaseModifyScheduledItemEdit):
    """Modify attributes and start and end overrides of repeat instance."""
    def __init__(
            self,
            scheduled_item,
            attr_dict):
        """Initialise edit.

        Args:
            scheduled_item (RepeatScheduledItemInstance): scheduled item to
                modify.
            attr_dict (dict(MutableAttribute, variant)): attributes to change.
        """
        subedits = []
        keep_last_for_inverse=[]
        if (scheduled_item._date in attr_dict
                or scheduled_item._start_time in attr_dict
                or scheduled_item._end_time in attr_dict):
            compute_override = SelfInverseSimpleEdit.create_unregistered(
                scheduled_item._compute_override,
            )
            subedits.append(compute_override)
            keep_last_for_inverse.append(compute_override)
        super(ModifyRepeatScheduledItemInstanceEdit, self).__init__(
            scheduled_item,
            attr_dict,
            subedits=subedits,
            keep_last_for_inverse=keep_last_for_inverse,
        )

    def _modified_attrs(self):
        """Get set of all attributes that are modified by edit.

        This ensures that overriding to the scheduled time isn't
        considered a valid edit if we started at the scheduled time
        already.

        Returns:
            (set(MutableAttribute)): set of modified attributes.
        """
        modified_attrs = super(
            ModifyRepeatScheduledItemInstanceEdit,
            self
        )._modified_attrs()

        date_key = self._scheduled_item._date
        start_key = self._scheduled_item._start_time
        end_key = self._scheduled_item._end_time
        sched_date = self._scheduled_item.scheduled_date
        sched_start = self._scheduled_item.scheduled_start_time
        sched_end = self._scheduled_item.scheduled_end_time
        key_schedule_tuples = [
            (date_key, sched_date),
            (start_key, sched_start),
            (end_key, sched_end),
        ]

        for key, sched_datetime in key_schedule_tuples:
            if key in modified_attrs:
                orig_datetime = self._original_attrs.get(key)
                new_datetime = self._attr_dict.get(key)
                if orig_datetime is None and new_datetime == sched_datetime:
                    modified_attrs.discard(key)
                elif new_datetime is None and orig_datetime == sched_datetime:
                    modified_attrs.discard(key)

        return modified_attrs


class ReplaceScheduledItemEdit(CompositeEdit):
    """Replace one scheduled item with another."""
    def __init__(self, old_scheduled_item, new_scheduled_item):
        """Initialise edit.

        Args:
            old_scheduled_item (BaseScheduledItem): scheduled item to replace.
            new_scheduled_item (BaseScheduledItem): scheduled item to replace
                it with.
        """
        remove_edit = RemoveScheduledItemEdit.create_unregistered(
            old_scheduled_item,
            deactivate=False,
        )
        switch_host_edit = ReplaceHostedDataEdit.create_unregistered(
            old_scheduled_item,
            new_scheduled_item,
        )
        add_edit = AddScheduledItemEdit.create_unregistered(
            new_scheduled_item,
            activate=False,
        )
        subedits = [remove_edit, switch_host_edit, add_edit]
        # task history update
        task_history_edits = _get_task_status_update_edits(
            old_scheduled_item=old_scheduled_item,
            new_scheduled_item=new_scheduled_item,
        )
        # TODO: is this ordering ok? or will the remove stuff not work
        # because the old one has been deactivated now?
        # and do we need to switch order for inverse?
        subedits.extend(task_history_edits)
        super(ReplaceScheduledItemEdit, self).__init__(subedits)
        self._is_valid = (old_scheduled_item != new_scheduled_item)

        self._callback_args = [
            old_scheduled_item,
            new_scheduled_item,
        ]
        self._undo_callback_args = [
            new_scheduled_item,
            old_scheduled_item,
        ]
        self._name = "ReplaceScheduledItem ({0})".format(
            old_scheduled_item.name
        )
        self._description = "Replace scheduled item {0} --> {1}".format(
            old_scheduled_item.name,
            new_scheduled_item.name,
        )


# TODO: delete this and all instances of it - now doing it all in modify edits
# class UpdateScheduledItemStatusEdit(CompositeEdit):
#     """Update check status of scheduled edit."""
#     def __init__(self, scheduled_item, new_status):
#         """Initialise edit.

#         Args:
#             scheduled_item (BaseScheduledItem): scheduled item whose check
#                 status we should edit.
#             new_status (int): new status to change to.
#         """
#         subedits = []
#         attribute_edit = AttributeEdit.create_unregistered(
#             {scheduled_item._status: new_status}
#         )
#         subedits.append(attribute_edit)
#         for planned_item in scheduled_item.planned_items:
#             # TODO: make this method below
#             # planned_item_edit = SelfInverseSimpleEdit(
#             #     planned_item._update_status_from_scheduled_items
#             # )
#             # subedits.append(planned_item_edit)
#             pass
#         task_item = scheduled_item._get_task_to_update_at_datetime()
#         if task_item is not None:
#             date_time = scheduled_item.end_datetime
#             prev_task_status = task_item.history.get_influenced_status(
#                 date_time,
#                 scheduled_item,
#             )
#             new_task_status = scheduled_item.get_new_task_status(new_status)
#             if prev_task_status != new_task_status:
#                 remove_status = True if new_task_status is None else False
#                 task_edit = UpdateTaskHistoryEdit.create_unregistered(
#                     task_item,
#                     influencer=scheduled_item,
#                     old_datetime=date_time,
#                     new_datetime=date_time,
#                     new_status=new_task_status,
#                     remove_status=remove_status,
#                 )
#                 subedits.append(task_edit)

#         super(UpdateScheduledItemStatusEdit, self).__init__(subedits)
#         self._is_valid = (new_status != scheduled_item.status)
#         self._callback_args = self._undo_callback_args = [
#             scheduled_item,
#             scheduled_item,
#         ]
#         self._name = "UpdateScheduledItemStatusEdit ({0})".format(
#             scheduled_item.name
#         )
#         self._description = (
#             "Update check status of scheduled item {0} ({1} --> {2})".format(
#                 scheduled_item.name,
#                 scheduled_item.status,
#                 new_status,
#             )
#         )
