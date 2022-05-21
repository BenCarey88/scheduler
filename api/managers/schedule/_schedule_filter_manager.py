"""Calendar filter manager class to manage filtering scheduled items."""

from ._base_schedule_manager import BaseScheduleManager


class ScheduleFilterManager(BaseScheduleManager):
    """Calendar filter manager to maintain filter attrs for scheduled items."""
    def __init__(self, user_prefs, calendar, archive_calendar):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            archive_calendar (Calendar): archive calendar object.
        """
        super(ScheduleFilterManager, self).__init__(
            user_prefs,
            calendar,
            archive_calendar,
        )
