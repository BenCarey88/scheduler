"""Planner filter manager class to manage filtering planned items."""

from scheduler.api.filter.planner_filters import NoFilter, TaskTreeFilter
from ._base_planner_manager import BasePlannerManager


class PlannerFilterManager(BasePlannerManager):
    """Planner filter manager to maintain filter attrs for planned items."""
    def __init__(self, name, user_prefs, calendar, tree_manager):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
        """
        super(PlannerFilterManager, self).__init__(
            name,
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

    def iter_filtered_items(self, calendar_period):
        """Get filtered planned items for given calendar period.

        Args:
            calendar_period (BaseCalendarPeriod): period to check.

        Yield:
            (PlannedItem): filtered planned item.
        """
        for planned_item in calendar_period.iter_planned_items(self.filter):
            yield planned_item

    def get_filtered_items(self, calendar_period):
        """Get list of filtered planned items for calendar period.

        Args:
            calendar_period (BaseCalendarPeriod): period to check.

        Returns:
            (list(PlannedItem)): filtered planned items.
        """
        return list(self.iter_filtered_items(calendar_period))
