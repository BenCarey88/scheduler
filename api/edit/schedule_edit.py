"""Calendar edits to be applied to scheduled items.

Friend classes: [Calendar, CalendarPeriod, ScheduledItem]
"""

from ._container_edit import ListEdit, ContainerOp, ContainerEditFlag
from ._core_edits import (
    AttributeEdit,
    CompositeEdit,
    SelfInverseSimpleEdit, 
    HostedDataEdit,
)


class AddScheduledItemEdit(ListEdit):
    """Add scheduled item to calendar."""
    def __init__(self, scheduled_item):
        """Initialise edit.

        Args:
            scheduled_item (BaseScheduledItem): the scheduled item to add. Can
                be a single scheduled item instance or a repeating item.
        """
        super(AddScheduledItemEdit, self).__init__(
            scheduled_item.get_item_container(),
            [scheduled_item],
            ContainerOp.ADD,
        )
        self._callback_args = self._undo_callback_args = [scheduled_item]
        self._name = "AddScheduledItem ({0})".format(scheduled_item.name)
        self._description = (
            "Add {0} {1} at {2}".format(
                scheduled_item.__class__.__name__,
                scheduled_item.name,
                scheduled_item.datetime_string(),
            )
        )


class RemoveScheduledItemEdit(ListEdit):
    """Remove scheduled item from calendar."""
    def __init__(self, scheduled_item):
        """Initialise edit.

        Args:
            scheduled_item (BaseScheduledItem): scheduled item to remove. Can be
                a single item or a repeat template.
        """
        super(RemoveScheduledItemEdit, self).__init__(
            scheduled_item.get_item_container(),
            [scheduled_item],
            ContainerOp.REMOVE,
            edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
        )
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

    def _check_validity(self):
        """Check if edit is valid."""
        self._is_valid = bool(self._modified_attrs())

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

    def _update(
            self,
            new_date=None,
            new_start_time=None,
            new_end_time=None,
            edit_replacements=None,
            edit_additions=None):
        """Update parameters of edit and run.

        Args:
            new_date (Date or None): new override date.
            new_start_time (Time or None): new override start time.
            new_end_time (Time or None): new override end time.
            edit_replacements (dict or None): dict of edit replacements to
                pass to superclass _update if needed.
            edit_additions (list or None): list of edit additions to pass to
                superclass _update if needed.
        """
        if (new_date is None
                and new_start_time is None
                and new_end_time is None):
            return

        edit_updates = {}
        attr_updates = {}
        if new_date is not None:
            attr_updates[self._scheduled_item._date] = new_date
        if new_start_time is not None:
            attr_updates[self._scheduled_item._start_time] = new_start_time
        if new_end_time is not None:
            attr_updates[self._scheduled_item._end_time] = new_end_time
        self._attr_dict.update(attr_updates)
        edit_updates[self._attribute_edit] = ([attr_updates], {})

        super(BaseModifyScheduledItemEdit, self)._update(
            edit_updates=edit_updates,
            edit_replacements=edit_replacements,
            edit_additions=edit_additions,
        )


class ModifyScheduledItemEdit(BaseModifyScheduledItemEdit):
    """Modify attributes and start and end datetimes of scheduled item.

    This edit can be performed continuously via drag and drop and hence must
    allow continuous editing to respond to user updates.
    """
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
            self._remove_edit = self._get_remove_edit(scheduled_item)
            self._add_edit = self._get_add_edit(scheduled_item, new_date)
            subedits.extend([self._remove_edit, self._add_edit])

        super(ModifyScheduledItemEdit, self).__init__(
            scheduled_item,
            attr_dict,
            subedits=subedits,
        )

    @staticmethod
    def _get_remove_edit(scheduled_item):
        """Get remove edit for moving scheduled item to new date.

        Args:
            scheduled_item (ScheduledItem): scheduled item to get edits for.

        Returns:
            (ListEdit): edit to remove scheduled item from old container.
        """
        return ListEdit.create_unregistered(
            scheduled_item.get_item_container(),
            [scheduled_item],
            ContainerOp.REMOVE,
            edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
        )

    @staticmethod
    def _get_add_edit(scheduled_item, new_date):
        """Get add edit for moving scheduled item to new date.

        Args:
            scheduled_item (ScheduledItem): scheduled item to get edit for.
            new_date (Date): date to move to.

        Returns:
            (ListEdit): edit to add scheduled item to new container.
        """
        return ListEdit.create_unregistered(
            scheduled_item.get_item_container(new_date),
            [scheduled_item],
            ContainerOp.ADD,
        )

    def _update(self, new_date=None, new_start_time=None, new_end_time=None):
        """Update parameters of edit and run.

        Args:
            new_date (Date or None): new date.
            new_start_time (Time or None): new start time.
            new_end_time (Time or None): new end time.
        """
        edit_replacements = {}
        edit_additions = []
        new_add_edit = None

        if new_date is not None:
            if self._add_edit is None:
                self._remove_edit = self._get_remove_edit(self._scheduled_item)
                self._add_edit = self._get_add_edit(
                    self._scheduled_item,
                    new_date
                )
                edit_additions.extend([self._remove_edit, self._add_edit])

            else:
                new_add_edit = self._get_add_edit(
                    self._scheduled_item,
                    new_date
                )
                edit_replacements[self._add_edit] = new_add_edit

        super(ModifyScheduledItemEdit, self)._update(
            new_date,
            new_start_time,
            new_end_time,
            edit_replacements=edit_replacements,
            edit_additions=edit_additions,
        )
        if new_add_edit is not None:
            self._add_edit = new_add_edit


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
    """Modify attributes and start and end overrides of repeat instance.

    This edit can be performed continuously via drag and drop and hence must
    allow continuous editing to respond to user updates.
    """
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

    def _update(self, new_date=None, new_start_time=None, new_end_time=None):
        """Update parameters of edit and run.

        Args:
            new_date (Date or None): new override date.
            new_start_time (Time or None): new override start time.
            new_end_time (Time or None): new override end time.
        """
        super(ModifyRepeatScheduledItemInstanceEdit, self)._update(
            new_date,
            new_start_time,
            new_end_time
        )
        self._scheduled_item._compute_override()


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
        )
        add_edit = AddScheduledItemEdit.create_unregistered(
            new_scheduled_item,
        )
        switch_host_edit = HostedDataEdit.create_unregistered(
            old_scheduled_item,
            new_scheduled_item,
        )
        super(ReplaceScheduledItemEdit, self).__init__(
            [remove_edit, add_edit, switch_host_edit],
        )

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
