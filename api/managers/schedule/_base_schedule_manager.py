"""Base calendar manager class."""

from scheduler.api.calendar.scheduled_item import(
    BaseScheduledItem,
    ScheduledItem,
    RepeatScheduledItem,
    RepeatScheduledItemInstance,
)

from .._base_manager import BaseCalendarManager, require_class


class BaseScheduleManager(BaseCalendarManager):
    """Base calendar manager class to build calendar managers from."""
    def __init__(self, user_prefs, calendar, archive_calendar):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            archive_calendar (Calendar): archive calendar object.
        """
        super(BaseScheduleManager, self).__init__(
            user_prefs,
            calendar,
            archive_calendar,
            name="schedule_manager",
        )

    @require_class((ScheduledItem, RepeatScheduledItemInstance), True)
    def get_item_to_modify(self, scheduled_item):
        """Get the scheduled item we can use to modify this one's attributes.

        Args:
            scheduled_item (ScheduledItem or RepeatScheduledItemInstance):
                scheduled item instance that a user can select.

        Returns:
            (BaseScheduledItem): either the scheduled item, or the repeat item
                that it's an instance of, in the case of repeat scheduled item
                instances.
        """
        if isinstance(scheduled_item, ScheduledItem):
            return scheduled_item
        elif isinstance(scheduled_item, RepeatScheduledItemInstance):
            return scheduled_item.repeat_scheduled_item

    @require_class((ScheduledItem, RepeatScheduledItem), True)
    def is_repeat_item(self, scheduled_item):
        """Check if item is repeat item or repeat item instance.

        Args:
            scheduled_item (ScheduledItem or RepeatScheduledItem): calendar
                item to check.

        Returns:
            (bool): whether or not item is repeat item.
        """
        return isinstance(scheduled_item, RepeatScheduledItem)

    @require_class((ScheduledItem, RepeatScheduledItem), True)
    def get_repeat_pattern(self, scheduled_item):
        """Get the repeat pattern of the scheduled item, if it's a repeat item.

        Args:
            scheduled_item (ScheduledItem or RepeatScheduledItem): scheduled item
                to check.

        Returns:
            (ScheduledItemRepeatPattern or None): repeat pattern.
        """
        if isinstance(scheduled_item, RepeatScheduledItem):
            return scheduled_item.repeat_pattern
        return None
