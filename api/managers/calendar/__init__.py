"""Calendar manager class."""

from ._calendar_edit_manager import CalendarEditManager
from ._calendar_filter_manager import CalendarFilterManager


class CalendarManager(CalendarEditManager, CalendarFilterManager):
    """Calendar edit manager to edit calendar items."""
    def __init__(self, user_prefs, calendar, archive_calendar=None):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar item.
            archive_calendar (Calendar): archive calendar object.
        """
        super(CalendarManager, self).__init__(
            user_prefs,
            calendar,
            archive_calendar,
        )
