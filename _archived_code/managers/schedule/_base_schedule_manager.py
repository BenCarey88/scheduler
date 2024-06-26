"""Base calendar manager class."""

from scheduler.api.calendar.scheduled_item import(
    BaseScheduledItem,
    ScheduledItem,
    ScheduledItemType,
    RepeatScheduledItem,
    RepeatScheduledItemInstance,
)

from .._base_manager import BaseCalendarManager, require_class


class BaseScheduleManager(BaseCalendarManager):
    """Base calendar manager class to build calendar managers from."""
    def __init__(self, name, user_prefs, calendar, tree_manager, filterer):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
            filterer (Filterer): filterer class for storing filters.
        """
        super(BaseScheduleManager, self).__init__(
            user_prefs,
            calendar,
            tree_manager,
            filterer=filterer,
            name=name,
            suffix="schedule_manager",
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

    @require_class(BaseScheduledItem, True)
    def has_task_type(self, scheduled_item, strict=False):
        """Check if item is a task item.

        Args:
            scheduled_item (ScheduledItem or RepeatScheduledItem): scheduled
                item to check.
            strict (bool): if True, don't include task categories.

        Returns:
            (bool): whether or not item is task item.
        """
        if not strict:
            return scheduled_item.type == ScheduledItemType.TASK
        return (
            scheduled_item.type == ScheduledItemType.TASK and
            scheduled_item.tree_item is not None and
            self._tree_manager.is_task(scheduled_item.tree_item)
        )

    @require_class(BaseScheduledItem, True)
    def has_event_type(self, scheduled_item):
        """Check if item is an event item.

        Args:
            scheduled_item (ScheduledItem or RepeatScheduledItem): scheduled
                item to check.

        Returns:
            (bool): whether or not item is an event item.
        """
        return scheduled_item.type == ScheduledItemType.EVENT

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
            (RepeatPattern or None): repeat pattern.
        """
        if isinstance(scheduled_item, RepeatScheduledItem):
            return scheduled_item.repeat_pattern
        return None
