"""Planner filter manager class to manage filtering planned items."""

from ._base_planner_manager import BasePlannerManager


class PlannerFilterManager(BasePlannerManager):
    """Planner filter manager to maintain filter attrs for planned items."""
    def __init__(self, user_prefs, calendar, tree_manager):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
        """
        super(PlannerFilterManager, self).__init__(
            user_prefs,
            calendar,
            tree_manager,
        )
