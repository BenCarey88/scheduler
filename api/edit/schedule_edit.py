"""Calendar edits to be applied to scheduled items.

Friend classes: [Calendar, CalendarPeriod, ScheduledItem]
"""

from scheduler.api.common.date_time import DateTime
from scheduler.api.enums import ItemStatus
from scheduler.api.utils import fallback_value

from ._container_edit import DictEdit, ListEdit, ContainerOp, ContainerEditFlag
from ._core_edits import (
    ActivateHostedDataEdit,
    AttributeEdit,
    DeactivateHostedDataEdit,
    CompositeEdit,
    ReplaceHostedDataEdit,
    SelfInverseSimpleEdit,
)
from ._base_calendar_item_edit import AddCalendarItemChildRelationshipEdit
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
                AddCalendarItemChildRelationshipEdit.create_unregistered(
                    parent,
                    scheduled_item,
                )
            )
            if not parent_edit._is_valid:
                super(AddScheduledItemEdit, self).__init__([])
                return
            parent_status_edit = SelfInverseSimpleEdit.create_unregistered(
                parent._update_status_from_children
            )
            subedits.extend([parent_edit, parent_status_edit])
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
        # update parent status from children
        for parent in scheduled_item._parents:
            parent_status_edit = SelfInverseSimpleEdit.create_unregistered(
                parent._update_status_from_children
            )
            subedits.append(parent_status_edit)
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

        The edit order is:
            1) attribute edit
            2) update parent statuses from children if needed
            3) task history edit
            4) add or remove override instances
            5) any subedits passed from superclass

        The inverse edit order is:
            5) subedits from superclass, except those in keep_last_for_inverse
            4) add or remove override instances
            3) task history edit
            2) update parent statuses from children if needed
            1) attribute edit
            6) any edits passed as keep_last_for_inverse

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

        # 5) subedits passed from superclass
        subedits = subedits or []

        # 1) attribute edit
        self._attribute_edit = AttributeEdit.create_unregistered(attr_dict)
        subedits.insert(0, self._attribute_edit)

        # 4) add or remove overrides if needed
        subedits[1:1] = self._get_override_update_edits()

        # 3) task history update edit
        subedits[1:1] = self._get_task_history_edits()

        # 2) update statuses from children if needed
        if scheduled_item._status in attr_dict:
            for parent in scheduled_item._parents:
                subedits[1:1] = [
                    SelfInverseSimpleEdit.create_unregistered(
                        parent._update_status_from_children
                    )
                ]

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

    # TODO: use this in _get_task_history_edits?
    def _get_new_attr(self, attr, fallback=None):
        """Convenience method to get value of attribute after the edit.

        Args:
            attr (MutableAttribute): attribute of the scheduled item.
            fallback (variant): the current value of that attribute on
                the item. This is only needed for cases where the property
                method is defined weirdly. Most of the time, we can just
                use attr.value to get the current value.
        """
        return fallback_value(
            self._attr_dict.get(attr),
            fallback_value(fallback, attr.value),
        )

    def _get_override_update_edits(self):
        """Get edits to add or remove overrides.

        This is used by repeat items and repeat scheduled items and must be
        overridden in these edit classes.

        Returns:
            (List(BaseEdit)): list of edits to update overrides.
        """
        return []

    @staticmethod
    def _get_task_history_edits_from_new_attributes(
            scheduled_item,
            new_date=None,
            new_start_time=None,
            new_end_time=None,
            new_task=None,
            new_status=None,
            new_update_policy=None,
            new_value_update=None):
        """Get task history edits for scheduled item after attribute edit.

        This is a static method that can be used by the implementations of
        _get_task_history_edits. This allows us to apply the logic to the
        scheduled item itself in the case of ScheduledItems and
        RepeatScheduledItemInstances, and to apply it just to instances of
        a RepeatScheduledItem.

        Args:
            scheduled_item (BaseScheduledItem): scheduled item we're finding
                task history edits for.
            new_date (Date or None): new date, if edited.
            new_start_time (Time or None): new start time, if edited.
            new_end_time (Time or None): new end time, if edited.
            new_task (BaseTaskItem or None): new task, if edited.
            new_status (ItemStatus or None): new status, if edited.
            new_update_policy (ItemUpdatePolicy or None): new update policy, if
                edited.
            new_value_update (variant or None): new value update, if edited.

        Returns:
            (list(UpdateTaskHistoryEdit)): list of edits to update task
                history.
        """
        edits = []

        # get original attribute values
        old_date = scheduled_item.date
        old_start_time = scheduled_item.start_time
        old_end_time = scheduled_item.end_time
        old_datetime = scheduled_item.end_datetime
        old_task = scheduled_item._get_task_to_update()
        old_task_status = None
        old_task_value = None
        if old_task is not None:
            old_task_status = old_task.history.get_influenced_status(
                old_datetime,
                scheduled_item,
            )
            old_task_value = old_task.history.get_influenced_value(
                old_datetime,
                scheduled_item,
            )

        # get new values or default to old
        new_date = fallback_value(new_date, old_date)
        new_start_time = fallback_value(new_start_time, old_start_time)
        new_end_time = fallback_value(new_end_time, old_end_time)
        new_datetime = DateTime.from_date_and_time(
            new_date,
            new_end_time,
        )
        new_task = fallback_value(new_task, old_task)
        _new_status = fallback_value(new_status, scheduled_item.status)
        _new_update_policy = fallback_value(
            new_update_policy,
            scheduled_item.task_update_policy,
        )
        _new_value_update = fallback_value(
            new_value_update,
            scheduled_item.task_value_update,
        )
        new_task_status = _new_update_policy.get_new_status(_new_status)
        new_task_value = scheduled_item._get_updated_value(
            new_value_update=_new_value_update,
            new_task=new_task,
            new_status=_new_status,
            new_start_time=new_start_time,
            new_end_time=new_end_time,
        )

        # case 1: remove from old task history and add to new task history
        if old_task != new_task:
            if (old_task is not None and
                    (old_task_status is not None
                     or old_task_value is not None)):
                remove_edit = UpdateTaskHistoryEdit.create_unregistered(
                    old_task,
                    influencer=scheduled_item,
                    old_datetime=old_datetime,
                )
                edits.append(remove_edit)
            if (new_task is not None and
                    (new_task_status is not None
                     or new_task_value is not None)):
                add_edit = UpdateTaskHistoryEdit.create_unregistered(
                    new_task,
                    influencer=scheduled_item,
                    new_datetime=new_datetime,
                    new_status=new_task_status,
                    new_value=new_task_value,
                )
                edits.append(add_edit)

        # case 2: update current task history
        elif (old_task is not None and
              (new_task_status != old_task_status or
               new_task_value != old_task_value or
               (old_datetime != new_datetime and
                (new_task_status is not None or new_task_value is not None)))):
            task_edit = UpdateTaskHistoryEdit.create_unregistered(
                old_task,
                influencer=scheduled_item,
                old_datetime=old_datetime,
                new_datetime=new_datetime,
                new_status=new_task_status,
                new_value=new_task_value,
                remove_status=(new_task_status is None),
                remove_value=(new_task_value is None)
            )
            edits.append(task_edit)
        return edits

    def _get_task_history_edits(self):
        """Get edits to update linked task history.

        This needs to be reimplemented for repeat items since the linked
        history there is actually dependent on its instances.

        Returns:
            (list(UpdateTaskHistoryEdit)): list of edits to update task
                history.
        """
        ad = self._attr_dict
        si = self._scheduled_item
        return self._get_task_history_edits_from_new_attributes(
            si,
            new_date=ad.get(si._date),
            new_start_time=ad.get(si._start_time),
            new_end_time=ad.get(si._end_time),
            new_task=si._get_task_to_update(
                new_type=ad.get(si._type),
                new_tree_item=ad.get(si._tree_item),
            ),
            new_status=ad.get(si._status),
            new_update_policy=ad.get(si._task_update_policy),
            new_value_update=ad.get(si._task_value_update),
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
        if (scheduled_item._date in attr_dict and
                attr_dict[scheduled_item._date] != scheduled_item.date):
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

        si = scheduled_item
        # if repeat pattern is updated, instances need to be recalculated
        if (scheduled_item._repeat_pattern in attr_dict): #and
                #atrr_dict[si._repeat_pattern] != si.repeat_pattern):
            clear_instances = SelfInverseSimpleEdit.create_unregistered(
                scheduled_item._clear_instances,
            )
            subedits.append(clear_instances)
            keep_last_for_inverse.append(clear_instances)

        super(ModifyRepeatScheduledItemEdit, self).__init__(
            scheduled_item,
            attr_dict,
            subedits=subedits,
            keep_last_for_inverse=keep_last_for_inverse,
        )

    def _get_override_update_edits(self):
        """Get edit to remove overrides.

        This checks whether items are still overrides or not and removes
        them as needed. Overrides need to be removed if they are overridden
        from dates that no longer exist in the repeat pattern, or if they
        no longer represent overrides.

        Returns:
            (list(BaseEdit)): edits to remove overrides, if needed.
        """
        overrides_dict = self._scheduled_item._overridden_instances
        si = self._scheduled_item
        new_repeat_pattern = self._get_new_attr(si._repeat_pattern)
        new_start_time = self._get_new_attr(si._start_time)
        new_end_time = self._get_new_attr(si._end_time)
        new_status = self._get_new_attr(si._status)

        override_removal_edits = []
        diff_dict = {}
        for date, instance in overrides_dict.items():
            # remove and deactivate if date no longer in repeat pattern
            if not new_repeat_pattern.check_date(date):
                diff_dict[instance.scheduled_date] = None
                deactivate_edit = DeactivateHostedDataEdit.create_unregistered(
                    instance
                )
                override_removal_edits.append(deactivate_edit)
            # or just remove it if it's no longer an override
            elif not instance.is_override(
                    template_start_time=new_start_time,
                    template_end_time=new_end_time,
                    template_status=new_status):
                diff_dict[instance.scheduled_date] = None

        if diff_dict:
            removal_edit = DictEdit.create_unregistered(
                overrides_dict,
                diff_dict,
                ContainerOp.REMOVE,
            )
            override_removal_edits.insert(0, removal_edit)

        return override_removal_edits

    def _get_task_history_edits(self):
        """Reimplement task history update edits.

        Since a repeat item can't influence statuses directly, and only
        does it through its instances, this instead checks through any
        instances of the item to see if they would be changed.

        Returns:
            (list(BaseEdit)): list of edits to update task history.
        """
        edits = []
        removed_instances = []
        si = self._scheduled_item
        ad = self._attr_dict
        # if instance no longer exists after edit, remove its history
        if si._repeat_pattern in ad:
            repeat_pattern = ad[si._repeat_pattern]
            for instance, task, date_time in si._iter_influences():
                if not repeat_pattern.check_date(instance.scheduled_date):
                    history_removal_edit = (
                        UpdateTaskHistoryEdit.create_unregistered(
                            task,
                            instance,
                            old_datetime=date_time,
                        )
                    )
                    edits.append(history_removal_edit)
                    removed_instances.append(instance)

        # if instance does exist after edit and its influence changes, edit it
        attributes_requiring_history_edits = [
            si._type,
            si._tree_item,
            si._task_update_policy,
            si._task_value_update,
        ]
        if (any(x in ad for x in attributes_requiring_history_edits)):
            # update policies currently can't be overridden by instances
            # so we can just get them from the repeat item's new value
            new_update_policy = ad.get(si._task_update_policy, None)
            new_value_update = ad.get(si._task_value_update, None)
            # Iterate only through overridden instances, as currently only these
            # ones are able to influence tasks.
            # NOTE we cannot use ItemUpdatePolicy.OVERRIDE for scheduled
            # item instances, as iter_overrides only looks at instances that
            # don't have an unstarted status
            for instance in si._iter_overrides():
                if instance in removed_instances:
                    continue
                new_edits = self._get_task_history_edits_from_new_attributes(
                    instance,
                    new_task=instance._get_task_to_update(
                        new_template_type=ad.get(si._type),
                        new_template_tree_item=ad.get(si._tree_item),
                    ),
                    new_update_policy=new_update_policy,
                    new_value_update=new_value_update,
                )
                edits.extend(new_edits)
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
        super(ModifyRepeatScheduledItemInstanceEdit, self).__init__(
            scheduled_item,
            attr_dict,
            subedits=subedits,
            keep_last_for_inverse=keep_last_for_inverse,
        )

    def _get_override_update_edits(self):
        """Get edit to add or remove overrides.

        This checks whether this is still an override and removes if not.

        Returns:
            (list(BaseEdit)): edits to remove overrides, if needed.
        """
        si = self._scheduled_item
        ri = si.repeat_scheduled_item
        overrides_dict = ri._overridden_instances

        new_date = self._get_new_attr(si._date)
        new_start_time = self._get_new_attr(si._start_time)
        new_end_time = self._get_new_attr(si._end_time)
        new_status = self._get_new_attr(si._status)

        is_override = si.is_override(
            instance_date=new_date,
            instance_start_time=new_start_time,
            instance_end_time=new_end_time,
            instance_status=new_status,
        )
        if not is_override and si in overrides_dict.values():
            # remove edit if no longer an override
            return [
                DictEdit.create_unregistered(
                    overrides_dict,
                    {si.scheduled_date: None},
                    ContainerOp.REMOVE,
                )
            ]
        if is_override and si not in overrides_dict.values():
            # add edit if it's become an override
            return [
                DictEdit.create_unregistered(
                    overrides_dict,
                    {si.scheduled_date: si},
                    ContainerOp.ADD,
                )
            ]
        return []

    def _modified_attrs(self):
        """Get set of all attributes that are modified by edit.

        This ensures that overriding to the scheduled date/time isn't
        considered a valid edit if we started at the scheduled date/time
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
