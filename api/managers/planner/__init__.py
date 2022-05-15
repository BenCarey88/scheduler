"""Planner manager class."""

from ._planner_edit_manager import PlannerEditManager
from ._planner_filter_manager import PlannerFilterManager


class PlannerManager(PlannerEditManager, PlannerFilterManager):
    """Planner edit manager to edit calendar items."""
    def __init__(self, user_prefs, calendar, archive_calendar=None):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar item.
            archive_calendar (Calendar): archive calendar object.
        """
        super(PlannerManager, self).__init__(
            user_prefs,
            calendar,
            archive_calendar,
        )
