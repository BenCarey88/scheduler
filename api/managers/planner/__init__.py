"""Planner manager class."""

from ._planner_edit_manager import PlannerEditManager
from ._planner_filter_manager import PlannerFilterManager


# TODO: these are becoming really cumbersome to update attributes of.
# would it not be possible to just pass a name and project attribute to each
# init and the get the other variables from there?
# And similarly in other parts of the code base too, eg. can default serializer
# code just use project objects directly too?
class PlannerManager(PlannerEditManager, PlannerFilterManager):
    """Planner manager to manage planned items."""
    def __init__(self, name, user_prefs, calendar, tree_manager, filterer):
        """Initialize class.

        Args:
            name (str): name of this manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            calendar (Calendar): calendar object.
            tree_manager (TreeManager): tree manager used by this tab.
            filterer (Filterer): filterer class for storing filters.
        """
        super(PlannerManager, self).__init__(
            name,
            user_prefs,
            calendar,
            tree_manager,
            filterer,
        )
