"""Calendar edits to be applied to scheduled items.

Friend classes: [Calendar, CalendarPeriod, ScheduledItem]
"""

# TODO: delete the commented out MutableHostedAttributes
# from scheduler.api.common.object_wrappers import MutableHostedAttribute
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


class AddScheduledItemAsChildEdit(CompositeEdit):
    """Add scheduled item and make it a child of the given planned item."""
    def __init__(self, scheduled_item, planned_item, index=None):
        """Initialise edit.

        Args:
            scheduled_item (BaseScheduledItem): the scheduled item to add.
            planned_item_parent (PlannedItem): the planned item to set as
                its parent.
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
            reverse_order_for_inverse=True):
        """Initialise edit.

        Args:
            scheduled_item (BaseScheduledItem): scheduled item to edit.
            attr_dict (dict(MutableAttribute, variant)): attributes to change.
            subedits (list(BaseEdit) or None): additional edits that subclasses
                may need for dealing with specific attribute changes.
            reverse_order_for_inverse (bool): whether or not inverse edit
                should reverse order of subedits.
        """
        updateable_attrs = [
            scheduled_item._start_time,
            scheduled_item._end_time,
            scheduled_item._date,
        ]
        self._scheduled_item = scheduled_item
        self._attr_dict = attr_dict
        self._original_attrs = {}
        for attr in list(attr_dict.keys()) + updateable_attrs:
            # note we need to record updateable attrs here for update to work
            self._original_attrs[attr] = attr.value

        self._attribute_edit = AttributeEdit.create_unregistered(attr_dict)
        subedits = subedits or []
        subedits.insert(0, self._attribute_edit)

        super(BaseModifyScheduledItemEdit, self).__init__(
            subedits,
            reverse_order_for_inverse=reverse_order_for_inverse,
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
        if scheduled_item._repeat_pattern in attr_dict:
            subedits.append(
                SelfInverseSimpleEdit.create_unregistered(
                    scheduled_item._clear_instances,
                )
            )
        if (scheduled_item._start_time in attr_dict
                or scheduled_item._end_time in attr_dict):
            subedits.append(
                SelfInverseSimpleEdit.create_unregistered(
                    scheduled_item._clean_overrides,
                )
            )
        super(ModifyRepeatScheduledItemEdit, self).__init__(
            scheduled_item,
            attr_dict,
            subedits=subedits,
            reverse_order_for_inverse=False,
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
        if (scheduled_item._date in attr_dict
                or scheduled_item._start_time in attr_dict
                or scheduled_item._end_time in attr_dict):
            subedits.append(
                SelfInverseSimpleEdit.create_unregistered(
                    scheduled_item._compute_override,
                )
            )
        super(ModifyRepeatScheduledItemInstanceEdit, self).__init__(
            scheduled_item,
            attr_dict,
            subedits=subedits,
            reverse_order_for_inverse=False,
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
        super(ReplaceScheduledItemEdit, self).__init__(
            [remove_edit, switch_host_edit, add_edit],
        )
        self._is_valid = (old_scheduled_item != new_scheduled_item)

        self._callback_args = [
            old_scheduled_item,
            new_scheduled_item,
        ]
        self._undo_callback_args = [
            new_scheduled_item,
            old_scheduled_item,
        ]
        self._name = "ReplaceScheduledItem ({0})".format(old_scheduled_item.name)
        self._description = "Replace scheduled item {0} --> {1}".format(
            old_scheduled_item.name,
            new_scheduled_item.name,
        )


class UpdateScheduledItemCheckStatusEdit(CompositeEdit):
    """Update check status of scheduled edit."""
    def __init__(self, scheduled_item, new_status, date_time):
        """Initialise edit.

        Args:
            scheduled_item (BaseScheduledItem): scheduled item whose check
                status we should edit.
            new_status (int): new status to change to.
            date_time (DateTime): the date and time this edit was done.
        """
        subedits = []
        attribute_edit = AttributeEdit.create_unregistered(
            {scheduled_item._status: new_status}
        )
        subedits.append(attribute_edit)
        for planned_item in scheduled_item.planned_items:
            planned_item_edit = SelfInverseSimpleEdit(
                planned_item._update_status_from_scheduled_items
            )
            subedits.append(planned_item_edit)
        if (scheduled_item.updates_task_status and
                scheduled_item.tree_item is not None):
            # TODO: check it's not a task category too? Or maybe remove
            # the not-None tree item check here and just require that both
            # these are checked in the manager class instead.
            task = scheduled_item.tree_item
            # TODO: DEFINE THE METHOD BELOW OR REMOVE IT
            new_task_status = task.get_new_status(new_status, date_time)
            # ^this method (maybe rename) should basically return the
            # new_status if it is higher than the current status of
            # the task at this time, otherwise return None.
            # Maybe need to deal with what happens if that status is
            # overridden at a later time (at least for non-routines)?
            #
            # ALSO need to deal with the case of cycling through the statuses
            # ie. if we set to in_progress then complete, then unstarted, the
            # unstarted should act to bring us back to where we began. So I
            # think we basically need to check: is there a task history at
            # this specific time? If so, then that specific task history should
            # just be removed when we go from complete to unstarted. Otherwise,
            # use the get_new_status function. This will need an update to the
            # way we store task history though as currently it only stores by
            # date.
            # EXCEPT: this doesn't work if the scheduled item is then moved.
            # so what we really need is a way for the task/task history to know
            # that the current status is influenced by this item. eg. give it
            # a status_influencers attribute, and if it's this item then we can
            # do the second thing, otherwise do the first.
            # eg _status_influencers = {
            #   sched_item_1: {
            #       date_time_1: IN_PROGRESS,
            #   },
            #   sched_item_2: {
            #       date_time_2: COMPLETE,
            #   },
            #   planned_item_1: {
            #       date_1: IN_PROGRESS,
            #   }
            # }
            # then moving sched_item_2 status -> unstarted means that we delete
            # it from the status influencers and update task history from the
            # remaining influencers? Could get slow with lots of influencers?
            if new_task_status is not None:
                # TODO: UPDATE THIS AND REMOVE THAT GOD-AWFUL COMMENT ABOVE
                task_edit = UpdateTaskHistoryEdit(
                    task,
                    date_time=date_time,
                    new_status=new_task_status,
                )
                subedits.append(task_edit)
        super(UpdateScheduledItemCheckStatusEdit, self).__init__(subedits)
        self._is_valid = (new_status != scheduled_item.status)
        self._callback_args = self._undo_callback_args = [
            scheduled_item,
            scheduled_item,
        ]
        self._name = "UpdateScheduledItemCheckStatusEdit ({0})".format(
            scheduled_item.name
        )
        self._description = (
            "Update check status of scheduled item {0} ({1} --> {2})".format(
                scheduled_item.name,
                scheduled_item.status,
                new_status,
            )
        )
