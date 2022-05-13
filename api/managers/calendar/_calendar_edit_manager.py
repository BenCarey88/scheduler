"""Calendar edit manager class to manage calendar item edits."""

from scheduler.api.edit.calendar_edit import (
    AddCalendarItemEdit,
    RemoveCalendarItemEdit,
    ModifyCalendarItemEdit,
    ModifyRepeatCalendarItemEdit,
    ModifyRepeatCalendarItemInstanceEdit,
    ReplaceCalendarItemEdit,
)
from scheduler.api.timetable.calendar_item import(
    BaseCalendarItem,
    CalendarItem,
    CalendarItemError,
    RepeatCalendarItem,
    RepeatCalendarItemInstance,
)
from scheduler.api.utils import fallback_value

from .._base_manager import require_class
from ._base_calendar_manager import BaseCalendarManager


class CalendarEditManager(BaseCalendarManager):
    """Calendar edit manager to apply edits to calendar items."""
    def __init__(self, user_prefs, calendar, archive_calendar):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar item.
            archive_calendar (Calendar): archive calendar object.
        """
        super(CalendarEditManager, self).__init__(
            user_prefs,
            calendar,
            archive_calendar,
        )
        self._item_being_moved = None
        self._continuous_edit = None

    def _create_calendar_item(self, item_class, *args, **kwargs):
        """Create calendar item and add to calendar.

        Args:
            item_class (class): calendar item to create
            *args (list): args to be passed to item init.
            **kwargs (dict): kwargs to be passed to item init.

        Returns:
            (CalendarItem): newly created calendar item.
        """
        item = item_class(*args, **kwargs)
        AddCalendarItemEdit.create_and_run(item)
        return item

    def create_calendar_item(self, *args, **kwargs):
        """Create single calendar item and add to calendar.

        Args:
            *args (list): args to be passed to CalendarItem init.
            **kwargs (dict): kwargs to be passed to CalendarItem init.

        Returns:
            (CalendarItem): newly created calendar item.
        """
        return self._create_calendar_item(CalendarItem, *args, **kwargs)

    def create_repeat_calendar_item(self, *args, **kwargs):
        """Create repeat calendar item and add to calendar.

        Args:
            *args (list): args to be passed to RepeatCalendarItem init.
            **kwargs (dict): kwargs to be passed to RepeatCalendarItem init.

        Returns:
            (RepeatCalendarItem): newly created calendar item.
        """
        return self._create_calendar_item(RepeatCalendarItem, *args, **kwargs)

    @require_class(BaseCalendarItem, True)
    def remove_calendar_item(self, calendar_item):
        """Remove calendar item from calendar.

        Args:
            calendar_item (BaseCalendarItem): calendar item to remove.
        """
        RemoveCalendarItemEdit.create_and_run(calendar_item)

    @require_class((CalendarItem, RepeatCalendarItem), raise_error=True)
    def modify_calendar_item(
            self,
            calendar_item,
            is_repeating,
            date=None,
            start_time=None,
            end_time=None,
            repeat_pattern=None,
            item_type=None,
            tree_item=None,
            event_category=None,
            event_name=None,
            is_background=None):
        """Modify calendar item.

        Args:
            calendar_item (BaseCalendarItem): item to edit.
            is_repeating (bool): whether or not to make this a repeating item.
            date (Date or None): new date.
            start_time (DateTime or None): new start date time.
            end_time (DateTime or None): new end date time.
            repeat_pattern (RepeatPattern or None): new repeat pattern.
            item_type (CalendarItemType or None): new type.
            tree_item (BaseTreeItem or None): new tree item.
            event_category (str or None): new category name.
            event_name (str or None): new event name.
            is_background (bool or None): new background value.
        """
        if is_repeating == isinstance(calendar_item, RepeatCalendarItem):
            # no class change needed, use ModifyCalendarItemEdit
            attr_dict = {
                calendar_item._date: date,
                calendar_item._start_time: start_time,
                calendar_item._end_time: end_time,
                calendar_item._repeat_pattern: repeat_pattern,
                calendar_item._type: item_type,
                calendar_item._tree_item: tree_item,
                calendar_item._event_category: event_category,
                calendar_item._event_name: event_name,
                calendar_item._is_background: is_background,
            }
            attr_dict = {
                attr: value
                for attr, value in attr_dict.items() if value is not None
            }
            edit_class = {
                CalendarItem: ModifyCalendarItemEdit,
                RepeatCalendarItem: ModifyRepeatCalendarItemEdit,
            }.get(type(calendar_item))
            if edit_class is None:
                raise CalendarItemError(
                    "Cannot modify calendar item of type {0}".format(
                        calendar_item.__class__.__name__
                    )
                )
            return edit_class.create_and_run(calendar_item, attr_dict)

        # otherwise a class change is needed, use ReplaceCalendarItemEdit
        date = fallback_value(date, calendar_item.date)
        start_time = fallback_value(start_time, calendar_item.start_time)
        end_time = fallback_value(end_time, calendar_item.end_time)
        repeat_pattern = fallback_value(
            repeat_pattern,
            calendar_item.repeat_pattern
        )
        item_type = fallback_value(item_type, calendar_item.type)
        tree_item = fallback_value(tree_item, calendar_item.tree_item)
        event_category = fallback_value(
            event_category,
            calendar_item.category
        )
        event_name = fallback_value(event_name, calendar_item.name)
        is_background = fallback_value(
            is_background,
            calendar_item.is_background
        )

        if is_repeating:
            new_calendar_item = RepeatCalendarItem(
                self._calendar,
                start_time,
                end_time,
                repeat_pattern,
                item_type=item_type,
                tree_item=tree_item,
                event_category=event_category,
                event_name=event_name,
                is_background=is_background,
            )
        else:
            new_calendar_item = CalendarItem(
                self._calendar,
                start_time,
                end_time,
                date,
                item_type=item_type,
                tree_item=tree_item,
                event_category=event_category,
                event_name=event_name,
                is_background=is_background,
                repeat_pattern=repeat_pattern,
            )
        ReplaceCalendarItemEdit.create_and_run(
            calendar_item,
            new_calendar_item,
        )

    @require_class((CalendarItem, RepeatCalendarItemInstance), True)
    def begin_move_item(
            self,
            calendar_item,
            date=None,
            start_time=None,
            end_time=None):
        """Move calendar item to new start and end datetimes.

        Args:
            calendar_item (BaseCalendarItem): item to edit.
            date (Date or None): new date.
            start_time (DateTime or None): new start date time.
            end_time (DateTime or None): new end date time.
        """
        # if date is None:
        #     date = calendar_item.date
        # if start_time is None:
        #     start_time = calendar_item.start_time
        # if end_time is None:
        #     end_time = calendar_item.end_time
        attr_dict = {
            calendar_item._date: date,
            calendar_item._start_time: start_time,
            calendar_item._end_time: end_time,
        }
        attr_dict = {
            attr: value
            for attr, value in attr_dict.items() if value is not None
        }
        edit_class = {
            CalendarItem: ModifyCalendarItemEdit,
            RepeatCalendarItemInstance: ModifyRepeatCalendarItemInstanceEdit,
        }.get(type(calendar_item))
        if edit_class is None:
            raise CalendarItemError(
                "Cannot modify calendar item of type {0}".format(
                    calendar_item.__class__.__name__
                )
            )
        self._continuous_edit = edit_class(calendar_item, attr_dict)
        self._item_being_moved = calendar_item
        self._continuous_edit.begin_continuous_run()

    @require_class((CalendarItem, RepeatCalendarItemInstance), True)
    def update_move_item(
            self,
            calendar_item,
            date=None,
            start_time=None,
            end_time=None):
        """Update edit to move calendar item to new start and end datetimes.

        Args:
            calendar_item (BaseCalendarItem): item to edit.
            date (Date or None): new date.
            start_time (DateTime or None): new start date time.
            end_time (DateTime or None): new end date time.
        """
        if self._continuous_edit is None:
            # TODO: sort exception
            raise CalendarItemError(
                "Cannot update edit when none is in progress."""
            )
        if self._item_being_moved != calendar_item:
            raise CalendarItemError(
                "item {0} is not currently being moved".format(
                    calendar_item.name
                )
            )
        self._continuous_edit.update_continuous_run(date, start_time, end_time)

    @require_class((CalendarItem, RepeatCalendarItemInstance), True)
    def end_move_item(self, calendar_item):
        """Finish edit to move calendar item to new start and end datetimes.

        Args:
            calendar_item (BaseCalendarItem): item to edit.
        """
        if self._continuous_edit is None:
            # TODO: sort exception
            raise CalendarItemError(
                "Cannot end edit when none is in progress."
            )
        if self._item_being_moved != calendar_item:
            raise CalendarItemError(
                "item {0} is not currently being moved".format(
                    calendar_item.name
                )
            )
        self._continuous_edit.end_continuous_run()
