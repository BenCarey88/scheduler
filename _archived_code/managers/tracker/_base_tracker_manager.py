"""Base tracker manager class."""

from .._base_manager import BaseCalendarManager


class BaseTrackerManager(BaseCalendarManager):
    """Base tracker manager class to build tracker managers from."""
    def __init__(
            self,
            name,
            user_prefs,
            calendar,
            tree_manager,
            filterer,
            tracker):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
            tracker (Tracker): tracker object.
            filterer (Filterer): filterer class for storing filters.
        """
        super(BaseTrackerManager, self).__init__(
            user_prefs,
            calendar,
            tree_manager,
            filterer=filterer,
            name=name,
            suffix="tracker_manager",
        )
        self._tracker = tracker

    @property
    def tracker(self):
        """Get tracker object.

        Returns:
            (Tracker): tracker object.
        """
        return self._tracker
