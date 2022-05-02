"""Calendar edits to be applied to calendar items.

Friend classes: [Calendar, CalendarPeriod, CalendarItem]
"""

# from functools import partial

# from scheduler.api.common.date_time import DateTime
# from scheduler.api.timetable.calendar_item import (
#     CalendarItem,
#     RepeatCalendarItem,
#     RepeatCalendarItemInstance
# )
from ._base_edit import BaseEdit, EditError
from ._container_edit import ListEdit, ContainerOp, ContainerEditFlag
from ._core_edits import (
    AttributeEdit,
    CompositeEdit,
    SelfInverseSimpleEdit, 
    HostedDataEdit,
)


# def _add_calendar_item(calendar, calendar_item):
#     """Add calendar item to calendar.

#     Args:
#         calendar (Calendar): calendar object.
#         calendar_item (CalendarItem): scheduled calendar item.
#     """
#     calendar_day = calendar.get_day(calendar_item.date)
#     calendar_day._scheduled_items.append(calendar_item)


# def _add_repeat_calendar_item(calendar, repeat_calendar_item):
#     """Add repeat calendar item to calendar.

#     Args:
#         calendar (Calendar): calendar object.
#         repeat_calendar_item (RepeatCalendarItem): repeat calendar item.
#     """
#     calendar._repeat_items.append(repeat_calendar_item)


# def _remove_calendar_item(calendar, calendar_item):
#     """Remove calendar item from calendar.

#     Args:
#         calendar (Calendar): calendar object.
#         calendar_item (CalendarItem): scheduled calendar item.
#     """
#     calendar_day = calendar.get_day(calendar_item.date)
#     try:
#         calendar_day._scheduled_items.remove(calendar_item)
#     except ValueError:
#         raise EditError(
#             "Calendar item {0} not stored in correct CalendarDay class".format(
#                 calendar_item.name
#             )
#         )


# def _remove_repeat_calendar_item(calendar, repeat_calendar_item):
#     """Remove calendar item from calendar.

#     Args:
#         calendar (Calendar): calendar object.
#         repeat_calendar_item (RepeatCalendarItem): repeat calendar item.
#     """
#     try:
#         calendar._repeat_items.remove(repeat_calendar_item)
#     except ValueError:
#         raise EditError(
#             "Repeat calendar item {0} not stored in calendar class".format(
#                 repeat_calendar_item.name
#             )
#         )


# def _move_calendar_item(
#         calendar,
#         calendar_item,
#         new_start_datetime,
#         new_end_datetime):
#     """Move calendar item to new datetime.

#     Args:
#         calendar (Calendar): calendar object.
#         calendar_item (CalendarItem): scheduled calendar item.
#         new_start_datetime (DateTime): new start datetime for calendar item.
#         new_end_datetime (DateTime): new end datetime for calendaritem.
#     """
#     old_day = calendar.get_day(calendar_item.date)
#     new_day = calendar.get_day(new_start_datetime.date())
#     calendar_item._start_datetime = new_start_datetime
#     calendar_item._end_datetime = new_end_datetime
#     try:
#         old_day._scheduled_items.remove(calendar_item)
#     except ValueError:
#         raise EditError(
#             "Calendar item {0} not stored in correct CalendarDay class".format(
#                 calendar_item.name
#             )
#         )
#     new_day._scheduled_items.append(calendar_item)


# def _move_repeat_calendar_item_instance(
#         calendar,
#         item_instance,
#         new_start_datetime,
#         new_end_datetime):
#     """Move repeat calendar item to new datetime.

#     Args:
#         calendar (Calendar): calendar object. Unused but passed for consistency
#             with _move_calendar_item function.
#         item_instance (RepeatCalendarItemInstance): repeat calendar item
#             instance.
#         new_start_datetime (DateTime): new start datetime for calendar item.
#         new_end_datetime (DateTime): new end datetime for calendaritem.
#     """
#     repeat_calendar_item = item_instance.repeat_calendar_item
#     scheduled_date = item_instance.scheduled_date
#     scheduled_start_datetime = DateTime.from_date_and_time(
#         scheduled_date,
#         repeat_calendar_item.start_time
#     )
#     scheduled_end_datetime = DateTime.from_date_and_time(
#         scheduled_date,
#         repeat_calendar_item.end_time
#     )
#     if new_start_datetime == scheduled_start_datetime:
#         new_start_datetime = None
#     if new_end_datetime == scheduled_end_datetime:
#         new_end_datetime = None

#     item_instance._override_start_datetime = new_start_datetime
#     item_instance._override_end_datetime = new_end_datetime
#     if (new_start_datetime is None and new_end_datetime is None and
#             repeat_calendar_item._overridden_instances.get(scheduled_date)):
#         del repeat_calendar_item._overridden_instances[scheduled_date]
#     else:
#         repeat_calendar_item._overridden_instances[scheduled_date] = (
#             item_instance
#         )


## IN PROCESS OF UPDATING TO USE CONTAINER AND ATTRIBUTE EDIT.
# class BaseCalendarEdit(CompositeEdit):
#     """Container edit on a calendar."""
#     def __init__(
#             self,
#             calendar,
#             diff_list,
#             op_type,
#             register_edit=True):
#         """Initialise edit.

#         Args:
#             calendar (Calendar): calendar object.
#             diff_list (list): list representing calendar items to add, remove
#                 or move.
#             op_type (ContainerOp): operation type. Note that this will
#                 interpret the operations differently from a standard list
#                 edit. See below.
#             register_edit (bool): whether or not to register this edit in the
#                 edit log (ie. whether or not it's a user edit that can be
#                 undone).

#         diff_list formats:
#             ADD:    [item]                  - add items to relevant container
#             REMOVE: [item]                  - remove items from container
#             MOVE:   [(item, new_datetime)]  - move items to new container
#             MODIFY: [(item, attr_dict)]     - modify item attributes
#         """
#         sub_edits = []
#         for item in diff_list:
#             # ADD: add item lsit edit
#             if op_type == ContainerOp.ADD:
#                 sub_edits.append(
#                     ListEdit(
#                         calendar.get_item_container(item),
#                         [item],
#                         op_type,
#                         register_edit=False,
#                     )
#                 )

#             # REMOVE: convert diff list to use indexes instead of items
#             elif op_type == ContainerOp.REMOVE:
#                 container = calendar.get_item_container(item)
#                 sub_edits.append(
#                     ListEdit(
#                         container,
#                         [container.index(item)],
#                         op_type,
#                         register_edit=False
#                     )
#                 )

#             # MOVE: remove from one container and add to new
#             elif op_type == ContainerOp.MOVE:
#                 # expand tuple
#                 item, new_datetime = item
#                 # remove items from old container
#                 old_container = calendar.get_item_container(item)
#                 sub_edits.append(
#                     ListEdit(
#                         old_container,
#                         [old_container.index(item)],
#                         ContainerOp.REMOVE,
#                         register_edit=False
#                     )
#                 )
#                 # edit item datetime attribute
#                 sub_edits.append(
#                     AttributeEdit(
#                         {item._datetime: new_datetime},
#                         register_edit=False,
#                     )
#                 )
#                 # add items to new container
#                 new_container = calendar.get_item_container(item, new_datetime)
#                 sub_edits.append(
#                     ListEdit(
#                         new_container,
#                         [item],
#                         ContainerOp.ADD,
#                         register_edit=False
#                     )
#                 )

#             # MODIFY: modify item attributes
#             elif op_type == ContainerOp.MODIFY:
#                 # expand tuple
#                 item, attr_dict = item
#                 # if datetime is edited, add move edit
#                 if item._datetime in attr_dict:
#                     sub_edits.append(
#                         BaseCalendarEdit(
#                             calendar,
#                             [item, attr_dict.get(item._datetime)],
#                             ContainerOp.MOVE,
#                             register_edit=False
#                         )
#                     )
#                     del attr_dict[item._datetime]
#                 # add attribute edit for other attributes
#                 sub_edits.append(
#                     AttributeEdit(
#                         attr_dict,
#                         register_edit=False,
#                     )
#                 )

#         super(BaseCalendarEdit, self).__init__(
#             sub_edits,
#             register_edit=register_edit
#         )


class AddCalendarItem(ListEdit):
    """Add calendar item to calendar."""
    def __init__(
            self,
            calendar_item,
            register_edit=True):
        """Initialise edit.

        Args:
            calendar_item (BaseCalendarItem): the calendar item to add. Can
                be a single calendar item instance or a repeating item.
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).
        """
        super(AddCalendarItem, self).__init__(
            calendar_item.get_item_container(),
            [calendar_item],
            ContainerOp.ADD,
            register_edit=register_edit,
        )
        self._name = "AddCalendarItem ({0})".format(calendar_item.name)
        self._description = (
            "Add {0} {1} at {2}".format(
                calendar_item.__class__.__name__,
                calendar_item.name,
                calendar_item.datetime_string(),
            )
        )


class RemoveCalendarItem(ListEdit):
    """Remove calendar item from calendar."""
    def __init__(
            self,
            calendar_item,
            register_edit=True):
        """Initialise edit.

        Args:
            calendar_item (BaseCalendarItem): calendar item to remove. Can be
                a single item or a repeat template.
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).
        """
        super(RemoveCalendarItem, self).__init__(
            calendar_item.get_item_container(),
            [calendar_item],
            ContainerOp.REMOVE,
            edit_flags=[ContainerEditFlag.REMOVE_BY_VALUE],
            register_edit=register_edit,
        )
        self._name = "RemoveCalendarItem ({0})".format(calendar_item.name)
        self._description = (
            "Remove {0} {1} at {2}".format(
                calendar_item.__class__.__name__,
                calendar_item.name,
                calendar_item.datetime_string(),
            )
        )


class BaseModifyCalendarItem(CompositeEdit):
    """Modify attributes (including date and time) of calendar item.

    This edit should not be called directly, instead there are subclasses
    for each different type of calendar item: standard, repeat and repeat
    instance.
    """
    def __init__(
            self,
            calendar_item,
            attr_dict,
            subedits=None,
            reverse_order_for_inverse=True,
            register_edit=True):
        """Initialise edit.

        Args:
            calendar_item (BaseCalendarItem): calendar item to edit.
            attr_dict (dict(MutableAttribute, variant)): attributes to change.
            subedits (list(BaseEdit) or None): additional edits that subclasses
                may need for dealing with specific attribute changes.
            reverse_order_for_inverse (bool): whether or not inverse edit
                should reverse order of subedits.
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).
        """
        self._calendar_item = calendar_item
        self._attr_dict = attr_dict
        self._original_attrs = {}
        for attr in attr_dict:
            self._original_attrs[attr] = attr.value
        self._check_validity()

        self._attribute_edit = AttributeEdit(attr_dict, register_edit=False)
        subedits = subedits or []
        subedits.insert(0, self._attribute_edit)

        super(BaseModifyCalendarItem, self).__init__(
            subedits,
            reverse_order_for_inverse=reverse_order_for_inverse,
            register_edit=register_edit,
        )
        self._name = "ModifyCalendarItem ({0})".format(calendar_item.name)

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

    def _get_attr_value_change_string(self, attr):
        """Get string describing value change for attribute.

        Args:
            attr (MutableAttribute): attribute to check.

        Returns:
            (str or None): string describing value change for attribute,
                unless attribute is unnamed, or value is unchanged, in which
                case return None.
        """
        if not attr.name:
            return None
        orig_value = self._original_attrs.get(attr, attr.value)
        new_value = self._attr_dict.get(attr, attr.value)
        if orig_value == new_value:
            return None
        return "{0}: {1} --> {2}".format(
            attr.name,
            str(orig_value),
            str(new_value)
        )

    @property
    def description(self):
        """Get description of item.

        Implemented as property so it stays updated. Note that this requires
        subclasses to implement _start_key and _end_key attributes.
        """
        attr_change_strings = [
            self._get_attr_value_change_string(attr)
            for attr in self._attr_dict
        ]
        return (
            "Edit attributes of {0} {1}:\n\t\t{2}".format(
                self._calendar_item.__class__.__name__,
                self._calendar_item.name,
                "\n\t\t".join([a for a in attr_change_strings if a])
            )
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
            attr_updates[self._calendar_item._date] = new_date
        if new_start_time is not None:
            attr_updates[self._calendar_item._start_time] = new_start_time
        if new_end_time is not None:
            attr_updates[self._calendar_item._end_time] = new_end_time
        self._attr_dict.update(attr_updates)
        edit_updates[self._attribute_edit] = ([attr_updates], {})

        super(ModifyRepeatCalendarItemInstance, self)._update(
            edit_updates=edit_updates,
            edit_replacements=edit_replacements,
            edit_additions=edit_additions,
        )
        self._check_validity()


class ModifyCalendarItem(BaseModifyCalendarItem):
    """Modify attributes and start and end datetimes of calendar item.

    This edit can be performed continuously via drag and drop and hence must
    allow continuous editing to respond to user updates.
    """
    def __init__(
            self,
            calendar_item,
            attr_dict,
            register_edit=True):
        """Initialise edit.

        Args:
            calendar_item (CalendarItem): calendar item to modify.
            attr_dict (dict(MutableAttribute, variant)): attributes to change.
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).
        """
        subedits = []
        self._remove_edit = None
        self._add_edit = None
        if calendar_item._date in attr_dict:
            new_date = attr_dict[calendar_item._date]
            # remove items from old container
            self._remove_edit = ListEdit(
                calendar_item.get_item_container(),
                [calendar_item],
                ContainerOp.REMOVE,
                edit_flags=[ContainerEditFlag.REMOVE_BY_VALUE],
                register_edit=False
            )
            # add items to new container
            self._add_edit = ListEdit(
                calendar_item.get_item_container(new_date),
                [calendar_item],
                ContainerOp.ADD,
                register_edit=False
            )
            subedits.extend([self._remove_edit, self._add_edit])

        super(ModifyCalendarItem, self).__init__(
            calendar_item,
            attr_dict,
            subedits=subedits,
            register_edit=register_edit,
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

        if new_date is not None:
            if self._add_edit is None:
                # remove items from old container
                self._remove_edit = ListEdit(
                    self._calendar_item.get_item_container(),
                    [self._calendar_item],
                    ContainerOp.REMOVE,
                    edit_flags=[ContainerEditFlag.REMOVE_BY_VALUE],
                    register_edit=False
                )
                # add items to new container
                self._add_edit = ListEdit(
                    self._calendar_item.get_item_container(new_date),
                    [self._calendar_item],
                    ContainerOp.ADD,
                    register_edit=False
                )
                edit_additions.extend([self._remove_edit, self._add_edit])

            else:
                edit_replacements[self._add_edit] = ListEdit(
                    self._calendar_item.get_item_container(new_date)
                    [self._calendar_item],
                    ContainerOp.ADD,
                    register_edit=False
                )

        super(ModifyCalendarItem, self)._update(
            new_date,
            new_start_time,
            new_end_time,
            edit_replacements=edit_replacements,
            edit_additions=edit_additions,
        )


class ModifyRepeatCalendarItem(BaseModifyCalendarItem):
    """Modify attributes of repeat calendar item."""
    def __init__(
            self,
            calendar_item,
            attr_dict,
            register_edit=True):
        """Initialise edit.

        Args:
            calendar_item (RepeatCalendarItem): calendar item to modify.
            attr_dict (dict(MutableAttribute, variant)): attributes to change.
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).
        """
        subedits = []
        if calendar_item._repeat_pattern in attr_dict:
            subedits.append(
                SelfInverseSimpleEdit(
                    calendar_item._clear_instances,
                    register_edit=False,
                )
            )
        if (calendar_item._start_time in attr_dict
                or calendar_item._end_time in attr_dict):
            subedits.append(
                SelfInverseSimpleEdit(
                    calendar_item._clean_overrides,
                    register_edit=False,
                )
            )
        super(ModifyRepeatCalendarItem, self).__init__(
            calendar_item,
            attr_dict,
            subedits=subedits,
            reverse_order_for_inverse=False,
            register_edit=register_edit,
        )


class ModifyRepeatCalendarItemInstance(BaseModifyCalendarItem):
    """Modify attributes and start and end overrides of repeat instance.

    This edit can be performed continuously via drag and drop and hence must
    allow continuous editing to respond to user updates.
    """
    def __init__(
            self,
            calendar_item,
            attr_dict,
            register_edit=True):
        """Initialise edit.

        Args:
            calendar_item (RepeatCalendarItemInstance): calendar item to
                modify.
            attr_dict (dict(MutableAttribute, variant)): attributes to change.
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).
        """
        subedits = []
        if (calendar_item._start_datetime in attr_dict
                or calendar_item._end_datetime in attr_dict):
            subedits.append(
                SelfInverseSimpleEdit(
                    calendar_item._clean_override,
                    register_edit=False,
                )
            )
        super(ModifyRepeatCalendarItemInstance, self).__init__(
            calendar_item,
            attr_dict,
            reverse_order_for_inverse=False,
            register_edit=register_edit,
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
            ModifyRepeatCalendarItemInstance,
            self
        )._modified_attrs()

        date_key = self._calendar_item._date
        start_key = self._calendar_item._start_time
        end_key = self._calendar_item._end_time
        sched_date = self._calendar_item.scheduled_date
        sched_start = self._calendar_item.scheduled_start_datetime
        sched_end = self._calendar_item.scheduled_end_datetime
        key_schedule_tuples = [
            (date_key, sched_date),
            (start_key, sched_start),
            (end_key, sched_end),
        ]

        for key, sched_datetime in key_schedule_tuples:
            if key in modified_attrs:
                orig_datetime = self._original_attrs.get(key)
                new_datetime = self._original_attrs.get(key)
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
        super(ModifyRepeatCalendarItemInstance, self)._update(
            new_date,
            new_start_time,
            new_end_time
        )
        self._calendar_item._clean_override()


# TODO better naming
class SwitchCalendarItem(CompositeEdit):
    """Switch one calendar item for another."""
    def __init__(
            self,
            old_calendar_item,
            new_calendar_item,
            register_edit=True):
        """Initialise edit.

        Args:
            old_calendar_item (CalendarItem): calendar item to replace.
            new_calendar_item (CalendarItem): calendar item to replace it with.
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).
        """
        subedits = []
        remove_edit = RemoveCalendarItem(
            old_calendar_item,
            register_edit=False,
        )
        add_edit = AddCalendarItem(
            new_calendar_item,
            register_edit=False,
        )
        switch_host_edit = HostedDataEdit(
            old_calendar_item,
            new_calendar_item,
            register_edit=False,
        )
        subedits.extend([remove_edit, add_edit, switch_host_edit])
        super(SwitchCalendarItem, self).__init__(
            subedits,
            register_edit=register_edit,
        )


class MakeCalendarItemRepeat(SwitchCalendarItem):
    """Make single calendar item a repeat item, and edit attrs."""
    def __init__(
            self,
            calendar_item,
            attr_dict,
            register_edit=True):
        """Initialise edit.

        Args:
            calendar_item (CalendarItem): calendar item.
            attr_dict (dict(MutableAttribute, variant)): additional attrs to
                edit.
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).
        """
        repeat_calendar_item = calendar_item.get_repeat_item(attr_dict)
        super(MakeCalendarItemRepeat, self).__init__(
            calendar_item,
            repeat_calendar_item,
            register_edit=register_edit,
        )


class MakeCalendarItemSingular(SwitchCalendarItem):
    """Make single calendar item a repeat item, and edit attrs."""
    def __init__(
            self,
            calendar_item,
            attr_dict,
            register_edit=True):
        """Initialise edit.

        Args:
            calendar_item (RepeatCalendarItem): calendar item.
            attr_dict (dict(MutableAttribute, variant)): additional attrs to
                edit.
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).
        """
        single_calendar_item = calendar_item.get_single_item(attr_dict)
        super(MakeCalendarItemRepeat, self).__init__(
            calendar_item,
            single_calendar_item,
            register_edit=register_edit,
        )


####################################################

# class AddCalendarItem(SimpleEdit):
#     """Add calendar item to calendar."""
#     def __init__(
#             self,
#             calendar,
#             calendar_item,
#             register_edit=True):
#         """Initialise edit.

#         Args:
#             calendar (Calendar): calendar object.
#             calendar_item (BaseCalendarItem): the calendar item to add. Can
#                 be a single calendar item instance or a repeating item.
#             register_edit (bool): whether or not to register this edit in the
#                 edit log (ie. whether or not it's a user edit that can be
#                 undone).
#         """
#         if isinstance(calendar_item, CalendarItem):
#             run_func = _add_calendar_item
#             inverse_run_func = _remove_calendar_item
#             start = calendar_item._start_datetime.string()
#             end = calendar_item._end_datetime.string()
#             item_name = "calendar item"
#         elif isinstance(calendar_item, RepeatCalendarItem):
#             run_func = _add_repeat_calendar_item
#             inverse_run_func = _remove_repeat_calendar_item
#             start = calendar_item._start_time.string()
#             end = calendar_item._end_time.string()
#             item_name = "repeat calendar item"
#         else:
#             raise EditError(
#                 "AddCalendarItem only accepts CalendarItem and "
#                 "RepeatCalendarItem inputs."
#             )

#         super(AddCalendarItem, self).__init__(
#             object_to_edit=calendar_item,
#             run_func=partial(run_func, calendar),
#             inverse_run_func=partial(inverse_run_func, calendar),
#             register_edit=register_edit
#         )
#         self._name = "AddCalendarItem ({0})".format(calendar_item.name)
#         self._description = (
#             "Add {0} {1} at ({2}, {3})".format(
#                 item_name,
#                 calendar_item.name,
#                 start,
#                 end,
#             )
#         )


# class RemoveCalendarItem(SimpleEdit):
#     """Remove calendar item from calendar."""
#     def __init__(
#             self,
#             calendar,
#             calendar_item,
#             register_edit=True):
#         """Initialise edit.

#         Args:
#             calendar (Calendar): calendar object.
#             calendar_item (BaseCalendarItem): calendar item to remove. Can be
#                 a single item or a repeat template.
#             register_edit (bool): whether or not to register this edit in the
#                 edit log (ie. whether or not it's a user edit that can be
#                 undone).
#         """
#         if isinstance(calendar_item, CalendarItem):
#             run_func = _remove_calendar_item
#             inverse_run_func = _add_calendar_item
#             start = calendar_item._start_datetime.string()
#             end = calendar_item._end_datetime.string()
#         elif isinstance(calendar_item, RepeatCalendarItem):
#             run_func = _remove_repeat_calendar_item
#             inverse_run_func = _add_repeat_calendar_item
#             start = calendar_item._start_time.string()
#             end = calendar_item._end_time.string()
#         else:
#             raise EditError(
#                 "RemoveCalendarItem only accepts CalendarItem and "
#                 "RepeatCalendarItem inputs."
#             )

#         super(RemoveCalendarItem, self).__init__(
#             object_to_edit=calendar_item,
#             run_func=partial(run_func, calendar),
#             inverse_run_func=partial(inverse_run_func, calendar),
#             register_edit=register_edit
#         )
#         self._name = "RemoveCalendarItem ({0})".format(calendar_item.name)
#         self._description = (
#             "Remove calendar item {0} at ({1}, {2})".format(
#                 calendar_item.name,
#                 start,
#                 end,
#             )
#         )


# # TODO: general point for all calendar item stuff (this module, calendar_item 
# # module and the dialog module) - I think it would be easier to pass dates and
# # times separately in these functions, as opposed to datetimes - that would
# # make it easier to reuse the same code when working with the repeat calendar
# # items (just miss out / ignore the date argument in that case)
# class ModifyCalendarItemDateTime(BaseEdit):
#     """Modify start and end datetimes of calendar item.

#     This edit can be performed continuously via drag and drop and hence must
#     allow continuous editing to respond to user updates. It can be applied to
#     either a standard CalendarItem object or a RepeatCalendarItemInstance.
#     """
#     def __init__(
#             self,
#             calendar,
#             calendar_item,
#             new_start_datetime=None,
#             new_end_datetime=None,
#             register_edit=True):
#         """Initialise edit.

#         Args:
#             calendar (Calendar): calendar object.
#             calendar_item (CalendarItem): scheduled calendar item.
#             new_start_datetime (DateTime or None): new start datetime for
#                 calendar item. If None, use original.
#             new_end_datetime (DateTime or None): new end datetime for calendar
#                 item. If None, use original.
#         """
#         super(ModifyCalendarItemDateTime, self).__init__(
#             register_edit=register_edit
#         )
#         self._calendar_item = calendar_item
#         self._calendar = calendar
#         if isinstance(calendar_item, RepeatCalendarItemInstance):
#             self._move_calendar_item_func = _move_repeat_calendar_item_instance
#             self._orig_start_datetime = calendar_item._start_datetime
#             self._orig_end_datetime = calendar_item._end_datetime
#         elif isinstance(calendar_item, CalendarItem):
#             self._move_calendar_item_func = _move_calendar_item
#             self._orig_start_datetime = calendar_item._start_datetime
#             self._orig_end_datetime = calendar_item._end_datetime
#         else:
#             raise EditError(
#                 "ModifyCalendarItem only accepts CalendarItem and "
#                 "RepeatCalendarItemInstance inputs."
#             )

#         self._new_start_datetime = (
#             new_start_datetime if new_start_datetime is not None
#             else self._orig_start_datetime
#         )
#         self._new_end_datetime = (
#             new_end_datetime if new_end_datetime is not None
#             else self._orig_end_datetime
#         )
#         self.check_validity()

#         self._name = "ModifyCalendarItemDateTime ({0})".format(
#             calendar_item.name
#         )

#     def check_validity(self):
#         """Set _is_valid attribute.

#         The edit is considered valid if it changes the time, otherwise it is
#         invalid and hence not added to the edit log.
#         """
#         self._is_valid = any([
#             self._new_start_datetime != self._orig_start_datetime,
#             self._new_end_datetime != self._orig_end_datetime
#         ])

#     @property
#     def description(self):
#         """Get description of edit.

#         Return
#             (str): description.
#         """
#         return (
#             "Edit attributes and move datetimes of {0}: "
#             "({1}, {2}) --> ({3}, {4})".format(
#                 self._calendar_item.name,
#                 self._orig_start_datetime.string(),
#                 self._orig_end_datetime.string(),
#                 self._new_start_datetime.string(),
#                 self._new_end_datetime.string()
#             )
#         )

#     def _run(self):
#         """Run edit."""
#         self._move_calendar_item_func(
#             self._calendar,
#             self._calendar_item,
#             self._new_start_datetime,
#             self._new_end_datetime
#         )

#     def _inverse_run(self):
#         """Run inverse to undo edit."""
#         self._move_calendar_item_func(
#             self._calendar,
#             self._calendar_item,
#             self._orig_start_datetime,
#             self._orig_end_datetime
#         )

#     def _update(self, new_start_datetime=None, new_end_datetime=None):
#         """Update parameters of edit and run.

#         Args:
#             new_start_datetime (DateTime or None): new start datetime.
#             new_end_datetime (DateTime or None): new end datetime.
#         """
#         if new_start_datetime is None and new_end_datetime is None:
#             return
#         if new_start_datetime is not None:
#             self._new_start_datetime = new_start_datetime
#         if new_end_datetime is not None:
#             self._new_end_datetime = new_end_datetime
#         self._move_calendar_item_func(
#             self._calendar,
#             self._calendar_item,
#             self._new_start_datetime,
#             self._new_end_datetime
#         )
#         self.check_validity()


# # TODO: add in check_validity to this edit
# class ModifyCalendarItem(CompositeEdit):
#     """Modify calendar item attributes.

#     This can be applied to either a CalendarItem or a RepeatCalendarItem.
#     """
#     def __init__(
#             self,
#             calendar,
#             calendar_item,
#             new_start_datetime=None,
#             new_end_datetime=None,
#             new_type=None,
#             new_tree_item=None,
#             new_event_category=None,
#             new_event_name=None,
#             new_is_background=None,
#             new_start_time=None,
#             new_end_time=None,
#             new_repeat_pattern=None,
#             register_edit=True,
#             **kwargs):
#         """Initialise edit.

#         Args:
#             calendar (Calendar): calendar object.
#             calendar_item (BaseCalendarItem): calendar item to edit.
#             new_start_datetime (DateTime or None): new start datetime for
#                 calendar item. If None, use original.
#             new_end_datetime (DateTime or None): new end datetime for calendar
#                 item. If None, use original.
#             new_type (CalendarItemType or None): type of calendar item, if
#                 we're changing it.
#             new_tree_item (Task or None): new tree item, if we're changing it.
#             new_event_category (Str or None): new name of event category, if
#                 changing.
#             new_event_name (str or None): new name of event, if changing.
#             new_is_background (bool or None): new value to set for
#                 _is_background attribute, if changing.
#             new_start_time (Time or None): new start time, if this is a repeat
#                 calendar item, and we're changing the start time.
#             new_end_time (Time or None): new end time, if this is a repeat
#                 calendar item, and we're changing the end time.
#             new_repeat_pattern (CalendarItemRepeatPattern or None): new repeat
#                 pattern object, if this is a repeat calendar item, and we're
#                 changing the repeat pattern.
#             register_edit (bool): whether or not to register this edit in the
#                 edit log (ie. whether or not it's a user edit that can be
#                 undone).
#             **kwargs (dict): kwargs to ignore.
#         """
#         self._calendar_item = calendar_item
#         self._calendar = calendar

#         self._orig_type = calendar_item._type
#         self._orig_tree_item = calendar_item._tree_item
#         self._orig_event_category = calendar_item._event_category
#         self._orig_event_name = calendar_item._event_name
#         self._orig_is_background = calendar_item._is_background

#         self._new_type = (
#             new_type if new_type is not None
#             else self._orig_type
#         )
#         self._new_tree_item = (
#             new_tree_item if new_tree_item is not None
#             else self._orig_tree_item
#         )
#         self._new_event_category = (
#             new_event_category if new_event_category is not None
#             else self._orig_event_category
#         )
#         self._new_event_name = (
#             new_event_name if new_event_name is not None
#             else self._orig_event_name
#         )
#         self._new_is_background = (
#             new_is_background if new_is_background is not None
#             else self._orig_is_background
#         )

#         base_edit = SimpleEdit(
#             object_to_edit=calendar_item,
#             run_func=self._base_edit_run,
#             inverse_run_func=self._base_edit_inverse_run,
#             register_edit=False
#         )

#         # Calendar Items
#         if isinstance(calendar_item, CalendarItem):
#             datetime_edit = ModifyCalendarItemDateTime(
#                 calendar,
#                 calendar_item,
#                 new_start_datetime,
#                 new_end_datetime,
#                 register_edit=False
#             )
#             super(ModifyCalendarItem, self).__init__(
#                 [base_edit, datetime_edit],
#                 register_edit=register_edit
#             )

#         # Repeat Calendar Items
#         else:
#             self._orig_start_time = calendar_item._start_time
#             self._orig_end_time = calendar_item._end_time
#             self._orig_repeat_pattern = calendar_item._repeat_pattern
#             self._new_start_time = (
#                 new_start_time if new_start_time is not None
#                 else self._orig_start_time
#             )
#             self._new_end_time = (
#                 new_end_time if new_end_time is not None
#                 else self._orig_end_time
#             )
#             self._new_repeat_pattern = (
#                 new_repeat_pattern if new_repeat_pattern is not None
#                 else self._orig_repeat_pattern
#             )
#             repeat_item_edit = SimpleEdit(
#                 object_to_edit=calendar_item,
#                 run_func=self._repeat_item_edit_run,
#                 inverse_run_func=self._repeat_item_edit_inverse_run,
#                 register_edit=False
#             )
#             super(ModifyCalendarItem, self).__init__(
#                 [base_edit, repeat_item_edit],
#                 register_edit=register_edit
#             )

#         self._name = "ModifyCalendarItem ({0})".format(
#             calendar_item.name
#         )
#         self._description = "Edit attributes of calendar item {0}".format(
#             self._calendar_item.name,
#         )

#     def _base_edit_run(self, calendar_item):
#         """Run base attribute edits.

#         These are the edits that can be run on both calendar items and repeat
#         calendar items.

#         Args:
#             calendar_item (BaseCalendarItem): calendar item to edit.
#         """
#         calendar_item._type = self._new_type
#         calendar_item._tree_item = self._new_tree_item
#         calendar_item._event_category = self._new_event_category
#         calendar_item._event_name = self._new_event_name
#         calendar_item._is_background = self._new_is_background

#     def _base_edit_inverse_run(self, calendar_item):
#         """Run base attributes inverse.
        
#         These are the edits that can be run on both calendar items and repeat
#         calendar items.

#         Args:
#             calendar_item (BaseCalendarItem): calendar item to edit.
#         """
#         calendar_item._type = self._orig_type
#         calendar_item._tree_item = self._orig_tree_item
#         calendar_item._event_category = self._orig_event_category
#         calendar_item._event_name = self._orig_event_name
#         calendar_item._is_background = self._orig_is_background

#     def _repeat_item_edit_run(self, calendar_item):
#         """Run edit on repeat calendar item attributes.

#         Args:
#             calendar_item (RepeatCalendarItem): repeat calendar item to edit.
#         """
#         calendar_item._start_time = self._new_start_time
#         calendar_item._end_time = self._new_end_time
#         if calendar_item._repeat_pattern != self._new_repeat_pattern:
#             calendar_item._repeat_pattern = self._new_repeat_pattern
#             calendar_item._clear_instances()
#         calendar_item._clean_overrides()

#     def _repeat_item_edit_inverse_run(self, calendar_item):
#         """Run inverse edit on repeat calendar item attributes.

#         Args:
#             calendar_item (RepeatCalendarItem): repeat calendar item to edit.
#         """
#         calendar_item._start_time = self._orig_start_time
#         calendar_item._end_time = self._orig_end_time
#         if calendar_item._repeat_pattern != self._orig_repeat_pattern:
#             calendar_item._repeat_pattern = self._orig_repeat_pattern
#             calendar_item._clear_instances()
#         calendar_item._clean_overrides()


# # TODO: this could be part of ModifyCalendarItem
# # plus wording is dodgy now repeat type has a different meaning in
# # calendar items module
# # TODO: also the __init__ args are VERY messy, needs cleaning
# class ChangeCalendarItemRepeatType(CompositeEdit):
#     """Change calendar item to repeating item or vice versa.

#     This also allows us to modify attribute values.
#     """
#     def __init__(
#             self,
#             calendar,
#             calendar_item,
#             date=None,
#             repeat_pattern=None,
#             new_start_datetime=None,
#             new_end_datetime=None,
#             new_type=None,
#             new_tree_item=None,
#             new_event_category=None,
#             new_event_name=None,
#             new_is_background=None,
#             new_start_time=None,
#             new_end_time=None,
#             register_edit=True,
#             **kwargs):
#         """Initialize edit.

#         Args:
#             calendar (Calendar): calendar object.
#             calendar_item (BaseCalendarItem): calendar item to edit.
#             date (Date or None): date of item, needed if switching from a
#                 repeat calendar item to a single one.
#             repeat_pattern (CalendarItemRepeatPattern or None): repeat pattern
#                 object, needed if switching to a repeat calendaritem.
#             register_edit (bool): whether or not to register this edit in the
#                 edit log (ie. whether or not it's a user edit that can be
#                 undone).

#             kwargs (dict): kwargs to ignore.
#         """
#         # TODO fallback_value would be a usefule util func
#         fallback_value = lambda v, f: v if v is not None else f

#         item_type = fallback_value(new_type, calendar_item._type)
#         tree_item = fallback_value(new_tree_item, calendar_item._tree_item)
#         event_category = fallback_value(
#             new_event_category,
#             calendar_item._event_category
#         )
#         event_name = fallback_value(new_event_name, calendar_item._event_name)
#         is_background = fallback_value(
#             new_is_background,
#             calendar_item._is_background
#         )

#         # Calendar Item --> Repeat Calendar Item
#         if isinstance(calendar_item, CalendarItem):
#             if repeat_pattern is None:
#                 raise EditError(
#                     "Need repeat pattern argument to switch calendar item to "
#                     "repeat calendar item."
#                 )
#             start_time = fallback_value(new_start_time, calendar_item.start_time)
#             end_time = fallback_value(new_end_time, calendar_item.end_time)
#             new_calendar_item = RepeatCalendarItem(
#                 calendar,
#                 start_time,
#                 end_time,
#                 repeat_pattern,
#                 item_type=item_type,
#                 tree_item=tree_item,
#                 event_category=event_category,
#                 event_name=event_name,
#                 is_background=is_background,
#             )
#         # Repeat Calendar Item --> Calendar Item
#         else:
#             if date is None:
#                 raise EditError(
#                     "Need date argument to switch repeat calendar item to "
#                     "calendar item."
#                 )
#             start_datetime = fallback_value(
#                 new_start_datetime,
#                 DateTime.from_date_and_time(date, calendar_item.start_time),
#             )
#             end_datetime = fallback_value(
#                 new_end_datetime,
#                 DateTime.from_date_and_time(date, calendar_item.end_time),
#             )
#             new_calendar_item = CalendarItem(
#                 calendar,
#                 start_datetime,
#                 end_datetime,
#                 item_type=item_type,
#                 tree_item=tree_item,
#                 event_category=event_category,
#                 event_name=event_name,
#                 is_background=is_background,
#             )

#         add_new_item_edit = AddCalendarItem(
#             calendar,
#             new_calendar_item,
#             register_edit=False
#         )
#         remove_old_item_edit = RemoveCalendarItem(
#             calendar,
#             calendar_item,
#             register_edit=False
#         )
#         super(ChangeCalendarItemRepeatType, self).__init__(
#             [add_new_item_edit, remove_old_item_edit],
#             register_edit=register_edit
#         )
