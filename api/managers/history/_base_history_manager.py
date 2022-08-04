"""Base history manager class."""

from .._base_manager import BaseCalendarManager


class BaseHistoryManager(BaseCalendarManager):
    """Base history manager class to build history managers from."""
    def __init__(self, name, user_prefs, calendar, tree_manager, filterer):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
            filterer (Filterer): filterer class for storing filters.
        """
        super(BaseHistoryManager, self).__init__(
            user_prefs,
            calendar,
            tree_manager,
            filterer=filterer,
            name=name,
            suffix="history_manager",
        )
