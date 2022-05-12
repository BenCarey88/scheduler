"""Base tree manager class."""

from scheduler.api.tree.task import Task
from scheduler.api.tree.task_category import TaskCategory

from .._base_manager import BaseManager


class BaseTreeManager(BaseManager):
    """Base tree manager class to build tree manager classes from."""
    def __init__(self, name, user_prefs, tree_root, archive_tree_root):
        """Initialize class.

        Args:
            name (str): name of tree manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            tree_root (TaskRoot): root task object.
            archive_tree_root (TaskRoot): root archive task object.
        """
        self._tree_root = tree_root
        self._archive_tree_root = archive_tree_root
        super(BaseTreeManager, self).__init__(
            user_prefs,
            name=name,
            suffix="tree_manager",
        )

    @property
    def tree_root(self):
        """Get tree root object.

        Returns:
            (TaskRoot): tree root object.
        """
        return self._tree_root

    @property
    def archive_tree_root(self):
        """Get archived tree root object.

        Returns:
            (TaskRoot): archived tree root object.
        """
        return self._archive_tree_root
