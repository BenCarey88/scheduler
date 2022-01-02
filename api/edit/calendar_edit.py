"""Calendar edits to be applied to calendar items.

Friend classes: [Calendar, CalendarPeriod, CalendarItem]
"""

from functools import partial

from scheduler.api.timetable.calendar_item import CalendarItem
from ._base_edit import BaseEdit, EditError
from ._core_edits import SimpleEdit


def _add_calendar_item(calendar, calendar_item):
    """Add calendar item to calendar.

    Args:
        calendar (Calendar): calendar object.
        calendar_item (CalendarItem): scheduled calendar item.
    """
    calendar_day = calendar.get_day(calendar_item.date)
    calendar_day._scheduled_items.append(calendar_item)


def _remove_calendar_item(calendar, calendar_item):
    """Remove calendar item from calendar.

    Args:
        calendar (Calendar): calendar object.
        calendar_item (CalendarItem): scheduled calendar item.
    """
    calendar_day = calendar.get_day(calendar_item.date)
    try:
        calendar_day._scheduled_items.remove(calendar_item)
    except ValueError:
        raise EditError(
            "Calendar item {0} not stored in correct CalendarDay class".format(
                calendar_item.name
            )
        )


def _move_calendar_item(
        calendar,
        calendar_item,
        new_start_datetime,
        new_end_datetime):
    """Move calendar item to new CalendarDay.

    Args:
        calendar (Calendar): calendar object.
        calendar_item (CalendarItem): scheduled calendar item.
        new_start_datetime (DateTime): new start datetime for calendar item.
        new_end_datetime (DateTime): new end datetime for calendaritem.
    """
    calendar_item._start_datetime = new_start_datetime
    calendar_item._end_datetime = new_end_datetime
    old_day = calendar.get_day(calendar_item.date)
    new_day = calendar.get_day(new_start_datetime.date)
    try:
        old_day._scheduled_items.remove(calendar_item)
    except ValueError:
        # TODO: (!) Maybe better to store all calendar_items in a giant
        # dictionary in calendar class, like with years, months, days? Keyed
        # by starting time, so this error wouldn't be needed.
        # But would need some way to distinguish multiple identical starting
        # times. Maybe key by (DateTime, id)? Or key by DateTime but make
        # values lists
        # but actually we still need to be able to list events by day so maybe
        # the current method does make the most sense.
        raise EditError(
            "Calendar item {0} not stored in correct CalendarDay class".format(
                calendar_item.name
            )
        )
    new_day._scheduled_items.append(calendar_item)


class AddCalendarItem(SimpleEdit):
    """Create calendar item and add to calendar."""
    def __init__(
            self,
            calendar,
            start_datetime=None,
            end_datetime=None,
            item_type=None,
            tree_item=None,
            event_category=None,
            event_name=None,
            register_edit=True):
        """Initialise edit.

        Args:
            calendar (Calendar): calendar object.
            calendar_item (CalendarItem): calendar item to schedule.
            start_datetime (DateTime): start datetime for calendar item.
            end_datetime (DateTime): end datetime for calendar item.
            type_ (CalendarItemType or None): type of calendar item,
                if setting.
            tree_item (Task or None): tree item, if setting.
            event_category (Str or None): nname of event category, if setting.
            event_name (str or None): name of event, if setting.
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).
        """
        calendar_item = CalendarItem(
            calendar,
            start_datetime,
            end_datetime,
            item_type,
            tree_item,
            event_category,
            event_name
        )
        super(BaseEdit, self).__init__(
            object_to_edit=calendar_item,
            run_func=partial(_add_calendar_item, calendar=calendar),
            inverse_run_func=partial(_remove_calendar_item, calendar=calendar),
            register_edit=register_edit
        )


class RemoveCalendarItem(SimpleEdit):
    """Remove calendar item from calendar."""
    def __init__(
            self,
            calendar,
            calendar_item,
            register_edit=True):
        """Initialise edit.

        Args:
            calendar (Calendar): calendar object.
            calendar_item (CalendarItem): calendar item to schedule.
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).
        """
        super(BaseEdit, self).__init__(
            object_to_edit=calendar_item,
            run_func=partial(_remove_calendar_item, calendar=calendar),
            inverse_run_func=partial(_add_calendar_item, calendar=calendar),
            register_edit=register_edit
        )


class ModifyCalendarItem(BaseEdit):
    """Modify start and end datetimes of calendar item, and item attributes.

    This edit can be performed continuously via drag and drop and hence must
    allow continuous editing to respond to user updates.
    """
    def __init__(
            self,
            calendar,
            calendar_item,
            new_start_datetime=None,
            new_end_datetime=None,
            new_type=None,
            new_tree_item=None,
            new_event_category=None,
            new_event_name=None,
            register_edit=True):
        """Initialise edit.

        Args:
            calendar (Calendar): calendar object.
            calendar_item (CalendarItem): scheduled calendar item.
            new_start_datetime (DateTime or None): new start datetime for
                calendar item. If None, use original.
            new_end_datetime (DateTime or None): new end datetime for calendar
                item. If None, use original.
            new_type (CalendarItemType or None): type of calendar item, if
                we're changing it.
            new_tree_item (Task or None): new tree item, if we're changing it.
            new_event_category (Str or None): new name of event category, if
                changing.
            new_event_name (str or None): new name of event, if changing.
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).
        """
        super(BaseEdit, self).__init__(register_edit=register_edit)
        self.calendar_item = calendar_item
        self.calendar = calendar

        self.orig_start_datetime = calendar_item._start_datetime
        self.orig_end_datetime = calendar_item._end_datetime
        self.orig_type = calendar_item._type
        self.orig_tree_item = calendar_item._tree_item
        self.orig_event_category = calendar_item._event_category
        self.orig_event_name = calendar_item._event_name

        self.new_start_datetime = (
            new_start_datetime if new_start_datetime is not None
            else self.orig_start_datetime
        )
        self.new_end_datetime = (
            new_end_datetime if new_end_datetime is not None
            else self.orig_end_datetime
        )
        self.new_type = (
            new_type if new_type is not None
            else self.orig_type
        )
        self.new_tree_item = (
            new_tree_item if new_tree_item is not None
            else self.orig_tree_item
        )
        self.new_event_category = (
            new_event_category if new_event_category is not None
            else self.orig_event_category
        )
        self.new_event_name = (
            new_event_name if new_event_name is not None
            else self.orig_event_name
        )
        self.check_validity()

        self._name = "ModifyCalendarItemDateTime ({0})".format(
            calendar_item.name
        )

    def check_validity(self):
        """Set _is_valid attribute.

        The edit is considered valid if it changes anything, otherwise it is
        invalid and hence not added to the edit log.
        """
        self._is_valid = any([
            self.new_start_datetime != self.orig_start_datetime,
            self.new_end_datetime != self.orig_end_datetime,
            self.new_type != self.orig_type,
            self.new_tree_item != self.orig_tree_item,
            self.new_event_category != self.orig_event_category,
            self.new_event_name != self.orig_event_name
        ])

    @property
    def description(self):
        """Get description of edit.

        Return description:
        """
        return "Move datetime of {0}: ({1}, {2}) --> ({3}, {4})".format(
            self.calendar_item.name,
            self.orig_start_datetime,
            self.orig_end_datetime,
            self.new_start_datetime,
            self.new_end_datetime
        )

    def _run(self):
        """Run edit."""
        _move_calendar_item(
            self.calendar,
            self.calendar_item,
            self.new_start_datetime,
            self.new_end_datetime
        )
        self.calendar_item._type = self.new_type
        self.calendar_item._tree_item = self.new_tree_item
        self.calendar_item._event_category = self.new_event_category
        self.calendar_item._event_name = self.new_event_name

    def _inverse_run(self):
        """Run inverse to undo edit."""
        _move_calendar_item(
            self.calendar,
            self.calendar_item,
            self.orig_start_datetime,
            self.orig_end_datetime
        )
        self.calendar_item._type = self.orig_type
        self.calendar_item._tree_item = self.orig_tree_item
        self.calendar_item._event_category = self.orig_event_category
        self.calendar_item._event_name = self.orig_event_name

    def _update(self, new_start_datetime=None, new_end_datetime=None):
        """Update parameters of edit and run.

        Args:
            new_start_datetime (DateTime or None): new start datetime.
            new_end_datetime (DateTime or None): new end datetime.
        """
        if new_start_datetime is None and new_end_datetime is None:
            return
        if new_start_datetime is not None:
            self.new_start_datetime = new_start_datetime
        if new_end_datetime is not None:
            self.new_end_datetime = new_end_datetime
        _move_calendar_item(
            self.calendar,
            self.calendar_item,
            self.new_start_datetime,
            self.new_end_datetime
        )
        self.check_validity()
