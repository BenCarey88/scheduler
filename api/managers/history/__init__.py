"""History manager class."""

from ._history_filter_manager import HistoryFilterManager


class HistoryManager(HistoryFilterManager):
    """History manager to manage history."""
    def __init__(self, name, user_prefs, calendar, tree_manager, filterer):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
            filterer (Filterer): filterer class for storing filters.
        """
        super(HistoryManager, self).__init__(
            name,
            user_prefs,
            calendar,
            tree_manager,
            filterer,
        )
