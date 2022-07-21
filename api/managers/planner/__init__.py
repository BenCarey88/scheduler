"""Planner manager class."""

from ._planner_edit_manager import PlannerEditManager
from ._planner_filter_manager import PlannerFilterManager


class PlannerManager(PlannerEditManager, PlannerFilterManager):
    """Planner manager to manage planned items."""
    def __init__(self, name, user_prefs, calendar, tree_manager):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
        """
        super(PlannerManager, self).__init__(
            name,
            user_prefs,
            calendar,
            tree_manager,
        )
