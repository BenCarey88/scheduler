"""History filter manager class."""

from scheduler.api.filter.history_filters import NoFilter, TaskTreeFilter
from ._base_history_manager import BaseHistoryManager


class HistoryFilterManager(BaseHistoryManager):
    """History filter manager to maintain filter attrs for planned items."""
    def __init__(self, name, user_prefs, calendar, tree_manager, filterer):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
            filterer (Filterer): filterer class for storing filters.
        """
        super(HistoryFilterManager, self).__init__(
            name,
            user_prefs,
            calendar,
            tree_manager,
            filterer,
        )

    @property
    def filter(self):
        """Get filter to filter history.

        Returns:
            (BaseFilter): filter to filter history items with.
        """
        if self._tree_manager.child_filter:
            return TaskTreeFilter(self._tree_manager.child_filter)
        return NoFilter()

    def get_filtered_tasks(self, calendar_day):
        """Get filtered list of tasks updated in given calendar day.

        Args:
            calendar_day (BaseCalendarDay): period to check.

        Returns:
            (list(BaseTaskItem)): list of tasks that were updated in given day.
        """
        history_dict = calendar_day.get_history_dict()
        with history_dict.apply_filter(self.filter):
            return [
                task for task, dict_ in history_dict.items() if dict_
            ]
