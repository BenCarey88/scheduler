"""Base planner manager class."""

from .._base_manager import BaseCalendarManager


class BasePlannerManager(BaseCalendarManager):
    """Base planner manager class to build planner managers from."""
    def __init__(self, user_prefs, calendar, archive_calendar):
        """Initialize class.

        Args:
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            archive_calendar (Calendar): archive calendar object.
        """
        super(BasePlannerManager, self).__init__(
            user_prefs,
            calendar,
            archive_calendar,
            name="planner_manager",
        )
