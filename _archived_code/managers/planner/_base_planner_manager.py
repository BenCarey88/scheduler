"""Base planner manager class."""

from .._base_manager import BaseCalendarManager


class BasePlannerManager(BaseCalendarManager):
    """Base planner manager class to build planner managers from."""
    def __init__(self, name, user_prefs, calendar, tree_manager, filterer):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
            filterer (Filterer): filterer class for storing filters.
        """
        super(BasePlannerManager, self).__init__(
            user_prefs,
            calendar,
            tree_manager,
            filterer=filterer,
            name=name,
            suffix="planner_manager",
        )
