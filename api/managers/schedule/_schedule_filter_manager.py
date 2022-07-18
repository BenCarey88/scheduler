"""Calendar filter manager class to manage filtering scheduled items."""

from scheduler.api.filter.schedule_filters import NoFilter, TaskTreeFilter
from scheduler.api.calendar.scheduled_item import BaseScheduledItem

from .._base_manager import require_class
from ._base_schedule_manager import BaseScheduleManager


class ScheduleFilterManager(BaseScheduleManager):
    """Calendar filter manager to maintain filter attrs for scheduled items."""
    def __init__(self, user_prefs, calendar, tree_manager):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
        """
        super(ScheduleFilterManager, self).__init__(
            user_prefs,
            calendar,
            tree_manager,
        )

    @property
    def filter(self):
        """Get filter to filter scheduled items.

        Returns:
            (BaseFilter): filter to filter scheduled items with.
        """
        if self._tree_manager.child_filter:
            return TaskTreeFilter(self._tree_manager.child_filter)
        return NoFilter()

    def iter_filtered_items(self, calendar_day):
        """Get filtered scheduled items for given day.

        Args:
            calendar_day (CalendarDay): day to check.

        Yield:
            (ScheduledItem or RepeatScheduledItemInstance): filtered scheduled
                items.
        """
        for scheduled_item in calendar_day.iter_scheduled_items(self.filter):
            yield scheduled_item
