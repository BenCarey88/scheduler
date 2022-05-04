"""Calendar filter manager class to manage filtering calendar items."""

from ._base_managers import BaseCalendarManager


class CalendarFilterManager(BaseCalendarManager):
    """Calendar filter manager to maintain filter attrs for calendar items."""
    def __init__(self, name, user_prefs, calendar, archive_calendar):
        """Initialize class.

        Args:
            name (str): name of tree manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar item.
            archive_calendar (Calendar): archive calendar object.
        """
        super(CalendarFilterManager, self).__init__(
            name,
            user_prefs,
            calendar,
            archive_calendar,
        )
