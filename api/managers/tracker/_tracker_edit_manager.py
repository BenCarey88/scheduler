"""Planner edit manager class to manage planned item edits."""

from .._base_manager import require_class
from ._base_tracker_manager import BaseTrackerManager


class TrackerEditManager(BaseTrackerManager):
    """Planner edit manager to apply edits to planned items."""
    def __init__(self, name, user_prefs, calendar, tree_manager, tracker):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
            tracker (Tracker): tracker object.
        """
        super(TrackerEditManager, self).__init__(
            name,
            user_prefs,
            calendar,
            tree_manager,
            tracker,
        )
