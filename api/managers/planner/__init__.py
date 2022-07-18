"""Planner manager class."""

from ._planner_edit_manager import PlannerEditManager
from ._planner_filter_manager import PlannerFilterManager


class PlannerManager(PlannerEditManager, PlannerFilterManager):
    """Planner edit manager to edit planned items."""
    def __init__(self, user_prefs, calendar, tree_manager):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
        """
        super(PlannerManager, self).__init__(
            user_prefs,
            calendar,
            tree_manager,
        )
