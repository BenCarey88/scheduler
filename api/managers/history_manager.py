"""History manager class."""

from scheduler.api.filter import FilterType

from ._base_manager import BaseCalendarManager


class HistoryManager(BaseCalendarManager):
    """History manager class to manage history edits."""
    def __init__(self, user_prefs, calendar): #, filter_manager):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
        """
        super(HistoryManager, self).__init__(
            user_prefs,
            calendar,
            filter_type=FilterType.HISTORY,
            name="history",
        )

    ### Filter Methods ###
    # @property
    # def filter(self):
    #     """Get filter to filter history.

    #     Returns:
    #         (BaseFilter): filter to filter history items with.
    #     """
    #     if self._filter_manager.tree_filter:
    #         return TaskTreeFilter(self._filter_manager.tree_filter)
    #     return NoFilter()

    def get_filtered_tasks(self, filter_manager, calendar_day):
        """Get filtered list of tasks updated in given calendar day.

        Args:
            filter_manager (FilterManager): filter manager to use.
            calendar_day (BaseCalendarDay): period to check.

        Returns:
            (list(BaseTaskItem)): list of tasks that were updated in given day.
        """
        history_dict = calendar_day.get_history_dict()
        with history_dict.apply_filter(self._get_filter(filter_manager)):
            return [
                task for task, dict_ in history_dict.items() if dict_
            ]
