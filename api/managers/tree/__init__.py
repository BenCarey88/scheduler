"""Tree manager class."""

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
