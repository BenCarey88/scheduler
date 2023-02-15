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


class AddScheduledItemEdit(CompositeEdit):
    """Add scheduled item to calendar."""
    def __init__(self, scheduled_item, parent=None, activate=True):
        """Initialise edit.

        Args:
            scheduled_item (BaseScheduledItem): the scheduled item to add. Can
                be a single scheduled item instance or a repeating item.
            parent (PlannedItem or None): planned item parent of scheduled
                item, if given.
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
        if parent is not None:
            parent_edit = (
                AddScheduledItemChildRelationshipEdit.create_unregistered(
                    scheduled_item,
                    parent,
                )
            )
            if not parent_edit._is_valid:
                super(AddScheduledItemEdit, self).__init__([])
                return
            subedits.append(parent_edit)
        super(AddScheduledItemEdit, self).__init__(subedits)
        self._callback_args = self._undo_callback_args = [scheduled_item]
        self._name = "AddScheduledItem ({0})".format(scheduled_item.name)
        self._description = (
            "Add {0} {1} at {2}{3}".format(
                scheduled_item.__class__.__name__,
                scheduled_item.name,
                scheduled_item.datetime_string(),
                " and make it a child of {0} {1}".format(
                    parent.__class__.__name__,
                    parent.name,
                ) if parent is not None else "",
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
        # task history update - remove all influences
        for item, task, date_time in scheduled_item._iter_influences():
            history_removal_edit = UpdateTaskHistoryEdit.create_unregistered(
                task,
                item,
                old_datetime=date_time,
            )
            subedits.append(history_removal_edit)
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
        self._scheduled_item = scheduled_item
        self._attr_dict = attr_dict
        self._original_attrs = {}
        for attr in list(attr_dict.keys()):
            self._original_attrs[attr] = attr.value
        subedits = subedits or []

        # attribute edit
        self._attribute_edit = AttributeEdit.create_unregistered(attr_dict)
        subedits.insert(0, self._attribute_edit)
        # task history update edit
        subedits[1:1] = self._get_task_history_edits()

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
        self._description = self._attribute_edit.get_description(
            self._scheduled_item,
            self._scheduled_item.name
        )

    def _modified_attrs(self):
        """Get set of all attributes that are modified by edit.

        Returns:
            (set(MutableAttribute)): set of modified attributes.
        """
        return set([
            attr for attr, value in self._attr_dict.items()
            if self._original_attrs.get(attr) != value
        ])
    
    def _get_task_history_edits(self):
        """Get edits to update linked task history.

        This needs to be reimplemented for repeat items since the linked
        history there is actually dependent on its instances.

        Returns:
            (list(UpdateTaskHistoryEdit)): list of edits to update task
                history.
        """
        edits = []
        ad = self._attr_dict
        si = self._scheduled_item

        # get old and new datetime, task and task status variables
        old_datetime = si.end_datetime
        old_task = si._get_task_to_update()
        old_task_status = None
        if old_task is not None:
            old_task_status = old_task.history.get_influenced_status(
                old_datetime,
                si,
            )
        new_datetime = DateTime.from_date_and_time(
            fallback_value(ad.get(si._date), si.date),
            fallback_value(ad.get(si._end_time), si.end_time),
        )
        new_task = si._get_task_to_update(
            new_type=ad.get(si._type),
            new_tree_item=ad.get(si._tree_item),
        )
        _new_status = fallback_value(ad.get(si._status), si.status)
        _new_update_policy = fallback_value(
            ad.get(si._update_policy),
            si.update_policy,
        )
        new_task_status = _new_update_policy.get_new_status(_new_status)

        # case 1: remove from old task history and add to new task history
        if old_task != new_task:
            if old_task_status is not None:
                remove_edit = UpdateTaskHistoryEdit.create_unregistered(
                    old_task,
                    influencer=si,
                    old_datetime=old_datetime,
                )
                edits.append(remove_edit)
            if new_task_status is not None:
                add_edit = UpdateTaskHistoryEdit.create_unregistered(
                    new_task,
                    influencer=si,
                    new_datetime=new_datetime,
                    new_status=new_task_status,
                )
                edits.append(add_edit)

        # case 2: update current task history
        elif (new_task_status != old_task_status or
                (new_task_status is not None and
                    old_datetime != new_datetime)):
            remove = True if new_task_status is None else False
            task_edit = UpdateTaskHistoryEdit.create_unregistered(
                old_task,
                influencer=si,
                old_datetime=old_datetime,
                new_datetime=new_datetime,
                new_status=new_task_status,
                remove_status=remove,
            )
            edits.append(task_edit)
        return edits


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
        elif (scheduled_item._start_time in attr_dict
                or scheduled_item._end_time in attr_dict
                or scheduled_item._status in attr_dict):
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

    def _get_task_history_edits(self):
        """Reimplement task history update edits.

        Since a repeat item can't influence statuses directly, and only
        does it through its instances, this just checks to see if any
        instances will be deleted by the edit and removes their linked
        histories.

        Returns:
            (list(BaseEdit)): list of edits to update task history.
        """
        edits = []
        removed_instances = []
        si = self._scheduled_item
        ad = self._attr_dict
        # if item no longer exists after edit, remove its history
        if si._repeat_pattern in ad:
            repeat_pattern = ad[si._repeat_pattern]
            for item, task, date_time in si._iter_influences():
                if not repeat_pattern.check_date(item.scheduled_end_datetime):
                    history_removal_edit = (
                        UpdateTaskHistoryEdit.create_unregistered(
                            task,
                            item,
                            old_datetime=date_time,
                        )
                    )
                    edits.append(history_removal_edit)
        # if item does exist after edit and its influence changes, edit it
        if si._update_policy in ad:
            update_policy = ad[si._update_policy]
            # NOTE we cannot use ItemUpdatePolicy.OVERRIDE for scheduled
            # item instances, as iter_overrides only looks at instances that
            # don't have an unstarted status
            for instance in si._iter_overrides():
                if instance in removed_instances:
                    continue
                date_time = instance.end_datetime
                task = instance._get_task_to_update(
                    new_template_type=ad.get(si._type),
                    new_template_tree_item=ad.get(si._tree_item),
                )
                old_task_status = task.history.get_influenced_status(
                    instance,
                    date_time,
                )
                new_task_status = update_policy.get_new_status(instance.status)
                if old_task_status != new_task_status:
                    history_edit = UpdateTaskHistoryEdit.create_unregistered(
                        task,
                        item,
                        old_datetime=date_time,
                        new_datetime=date_time,
                        new_status=new_task_status,
                    )
                    edits.append(history_edit)
        return edits


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
                or scheduled_item._end_time in attr_dict
                or scheduled_item._status in attr_dict):
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
        # task history update - remove all influences
        for item, task, date_time in old_scheduled_item._iter_influences():
            history_removal_edit = UpdateTaskHistoryEdit.create_unregistered(
                task,
                item,
                old_datetime=date_time,
            )
            subedits.insert(1, history_removal_edit)
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
