"""Planner filter manager class to manage filtering planned items."""

from ._base_planner_manager import BasePlannerManager


class PlannerFilterManager(BasePlannerManager):
    """Planner filter manager to maintain filter attrs for planned items."""
    def __init__(self, user_prefs, calendar, archive_calendar):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            archive_calendar (Calendar): archive calendar object.
        """
        super(PlannerFilterManager, self).__init__(
            user_prefs,
            calendar,
            archive_calendar,
        )
