"""Tracker manager class."""

# from scheduler.api.filter.tracker_filters import NoFilter, TaskTreeFilter
from scheduler.api.filter import FilterType, quasiconvert_filter

from ._base_manager import BaseCalendarManager


class TrackerManager(BaseCalendarManager):
    """Tracker manager class to manage tracker edits."""
    def __init__(self, user_prefs, calendar, tracker): # filter_manager, tracker):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tracker (Tracker): tracker object.    
        """
        super(TrackerManager, self).__init__(
            user_prefs,
            calendar,
            filter_type=FilterType.TRACKER, #TODO: merge this with tree type?
            name="tracker",
        )
        self._tracker = tracker

    @property
    def tracker(self):
        """Get tracker object.

        Returns:
            (Tracker): tracker object.
        """
        return self._tracker

    # ### Filter Methods ###
    # @property
    # def filter(self):
    #     """Get filter to filter tracked tasks.

    #     Returns:
    #         (BaseFilter): filter to filter tracked tasks with.
    #     """
    #     if self._filter_manager.tree_filter:
    #         return TaskTreeFilter(self._filter_manager.tree_filter)
    #     return NoFilter()

    def iter_filtered_items(self, filter_manager):
        """Get filtered tasks selected for tracking.

        Args:
            filter_manager (FilterManager): filter manager to use.

        Yields:
            (Task): filtered tracked tasks.
        """
        filter_ = self._get_filter(filter_manager)
        for task in self.tracker.iter_tracked_tasks(filter=filter_):
            yield task
