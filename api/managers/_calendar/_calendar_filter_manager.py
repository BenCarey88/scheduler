"""Calendar filter manager class to manage filtering calendar items."""

from ._base_calendar_manager import BaseCalendarManager


class CalendarFilterManager(BaseCalendarManager):
    """Calendar filter manager to maintain filter attrs for calendar items."""
    def __init__(self, user_prefs, calendar, archive_calendar):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar item.
            archive_calendar (Calendar): archive calendar object.
        """
        super(CalendarFilterManager, self).__init__(
            user_prefs,
            calendar,
            archive_calendar,
        )
