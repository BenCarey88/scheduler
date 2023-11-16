"""History manager class."""

from ._base_manager import BaseCalendarManager


class HistoryManager(BaseCalendarManager):
    """History manager class to manage history edits."""
    def __init__(self, name, user_prefs, calendar, filter_manager):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            filter_manager (FilterManager): filter manager class for managing
                filters.
        """
        super(HistoryManager, self).__init__(
            user_prefs,
            calendar,
            filter_manager=filter_manager,
            name=name,
            suffix="history_manager",
        )
