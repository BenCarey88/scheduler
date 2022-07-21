"""Base history manager class."""

from .._base_manager import BaseCalendarManager


class BaseHistoryManager(BaseCalendarManager):
    """Base history manager class to build history managers from."""
    def __init__(self, name, user_prefs, calendar, tree_manager):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
        """
        super(BaseHistoryManager, self).__init__(
            user_prefs,
            calendar,
            tree_manager,
            name=name,
            suffix="history_manager",
        )
