"""Planner filter manager class to manage filtering planned items."""

from ._base_planner_manager import BasePlannerManager


class PlannerFilterManager(BasePlannerManager):
    """Planner filter manager to maintain filter attrs for calendar items."""
    def __init__(self, user_prefs, calendar, archive_calendar):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar item.
            archive_calendar (Calendar): archive calendar object.
        """
        super(PlannerFilterManager, self).__init__(
            user_prefs,
            calendar,
            archive_calendar,
        )
