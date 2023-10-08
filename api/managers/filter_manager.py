"""Filter manager for managing filtering."""

from ._base_manager import require_class, BaseManager


class FilterManager(BaseManager):
    """Filter manager to filter items and apply filter edits."""
    def __init__(self, name, user_prefs, tree_root, filterer):
        """Initialise class.

        Args:
            name (str): name of tree manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            tree_root (TaskRoot): root task object.
            filterer (Filterer): filterer class for storing filters.
        """
        self._tree_root = tree_root
        self._archive_tree_root = tree_root.archive_root
        super(FilterManager, self).__init__(
            user_prefs,
            filterer=filterer,
            name=name,
            suffix="filter_manager",
        )
