"""Tracker manager class."""

from ._base_manager import BaseCalendarManager


class TrackerManager(BaseCalendarManager):
    """Tracker manager class to manage tracker edits."""
    def __init__(self, name, user_prefs, calendar, filter_manager, tracker):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tracker (Tracker): tracker object.
            filter_manager (FilterManager): filter manager class for managing
                filters.
        """
        super(TrackerManager, self).__init__(
            user_prefs,
            calendar,
            filter_manager=filter_manager,
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
