"""Managers for managing edits and filter/ui functionality of other classes."""


from ._calendar_edit_manager import CalendarEditManager
from ._calendar_filter_manager import CalendarFilterManager
from ._tree_edit_manager import TreeEditManager
from ._tree_filter_manager import TreeFilterManager


class TreeManager(TreeEditManager, TreeFilterManager):
    """Tree manager class."""
    def __init__(self, name, user_prefs, tree_root, archive_tree_root=None):
        """Initialise tree manager.

        Args:
            name (str): name of tree manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            tree_root (TaskRoot): root task object.
            archive_tree_root (TaskRoot): root archive task object
        """
        super(TreeManager, self).__init__(
            name,
            user_prefs,
            tree_root,
            archive_tree_root
        )


class CalendarManager(CalendarEditManager, CalendarFilterManager):
    """Calendar edit manager to edit calendar items."""
    def __init__(self, name, user_prefs, calendar, archive_calendar=None):
        """Initialize class.

        Args:
            name (str): name of tree manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar item.
            archive_calendar (Calendar): archive calendar object.
        """
        super(CalendarManager, self).__init__(
            name,
            user_prefs,
            calendar,
            archive_calendar,
        )
