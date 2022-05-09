"""Base calendar manager class."""

from scheduler.api.timetable.calendar_item import(
    BaseCalendarItem,
    CalendarItem,
    RepeatCalendarItem,
    RepeatCalendarItemInstance,
)

from .._base_manager import BaseManager, require_class


class BaseCalendarManager(BaseManager):
    """Base calendar manager class to build calendar managers from."""
    def __init__(self, user_prefs, calendar, archive_calendar):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            archive_calendar (Calendar): archive calendar object.
        """
        self._calendar = calendar
        self._archive_calendar = archive_calendar
        super(BaseCalendarManager, self).__init__(
            user_prefs,
            suffix="calendar_manager",
        )

    @property
    def calendar(self):
        """Get calendar object.

        Returns:
            (Calendar): calendar object.
        """
        return self._calendar

    @property
    def archive_calendar(self):
        """Get archived calendar object.

        Returns:
            (Calendar): archived calendar object.
        """
        return self._archive_calendar

    @require_class((CalendarItem, RepeatCalendarItemInstance), True)
    def get_item_to_modify(self, calendar_item):
        """Get the calendar item we can use to modify this one's attributes.

        Args:
            calendar_item (CalendarItem or RepeatCalendarItemInstance):
                calendar item instance that a user can select.

        Returns:
            (BaseCalendarItem): either the calendar item, or the repeat item
                that it's an instance of, in the case of repeat calendar item
                instances.
        """
        if isinstance(calendar_item, CalendarItem):
            return calendar_item
        elif isinstance(calendar_item, RepeatCalendarItemInstance):
            return calendar_item.repeat_calendar_item

    @require_class((CalendarItem, RepeatCalendarItem), True)
    def is_repeat_item(self, calendar_item):
        """Check if item is repeat item or repeat item i.

        Args:
            calendar_item (CalendarItem or RepeatCalendarItem): calendar
                item to check.

        Returns:
            (bool): whether or not item is repeat item.
        """
        return isinstance(calendar_item, RepeatCalendarItem)

    @require_class((CalendarItem, RepeatCalendarItem), True)
    def get_repeat_pattern(self, calendar_item):
        """Get the repeat pattern of the calendar item, if it's a repeat item.

        Args:
            calendar_item (CalendarItem or RepeatCalendarItem): calendar item
                to check.

        Returns:
            (CalendarItemRepeatPattern or None): repeat pattern.
        """
        if isinstance(calendar_item, RepeatCalendarItem):
            return calendar_item.repeat_pattern
        return None
