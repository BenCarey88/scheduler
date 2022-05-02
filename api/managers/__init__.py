"""Managers for managing edits and filter/ui functionality of other classes."""


from ._tree_edit_manager import TreeEditManager
from ._tree_filter_manager import TreeFilterManager


class TreeManager(TreeEditManager, TreeFilterManager):
    """Tree manager class."""
    def __init__(self, name, user_prefs, tree_root):
        """Initialise tree manager.

        Args:
            name (str): name of tree manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            tree_root (TaskRoot): root task object.
        """
        super(TreeManager, self).__init__(name, user_prefs, tree_root)
