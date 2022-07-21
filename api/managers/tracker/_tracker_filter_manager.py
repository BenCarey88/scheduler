"""Tracker filter manager class."""

from scheduler.api.filter.tracker_filters import NoFilter, TaskTreeFilter
from ._base_tracker_manager import BaseTrackerManager


class TrackerFilterManager(BaseTrackerManager):
    """Tracker filter manager to maintain filter attrs for tracked items."""
    def __init__(self, name, user_prefs, calendar, tree_manager, tracker):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
            tracker (Tracker): tracker object.
        """
        super(TrackerFilterManager, self).__init__(
            name,
            user_prefs,
            calendar,
            tree_manager,
            tracker,
        )

    @property
    def filter(self):
        """Get filter to filter tracked tasks.

        Returns:
            (BaseFilter): filter to filter tracked tasks with.
        """
        if self._tree_manager.child_filter:
            return TaskTreeFilter(self._tree_manager.child_filter)
        return NoFilter()

    def iter_filtered_tracked_tasks(self):
        """Get filtered tasks selected for tracking.

        Yields:
            (Task): filtered tracked tasks.
        """
        for task in self.tracker.iter_tracked_tasks(filter=self.filter):
            yield task
