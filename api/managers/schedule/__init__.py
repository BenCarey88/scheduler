"""Planner manager class."""

from ._schedule_edit_manager import ScheduleEditManager
from ._schedule_filter_manager import ScheduleFilterManager


class ScheduleManager(ScheduleEditManager, ScheduleFilterManager):
    """Calendar edit manager to edit scheduled items."""
    def __init__(self, name, user_prefs, calendar, tree_manager, filterer):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
            filterer (Filterer): filterer class for storing filters.
        """
        super(ScheduleManager, self).__init__(
            name,
            user_prefs,
            calendar,
            tree_manager,
            filterer,
        )
