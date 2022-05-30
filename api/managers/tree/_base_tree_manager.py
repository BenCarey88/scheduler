"""Base tree manager class."""

from scheduler.api.tree._base_tree_item import BaseTreeItem
from scheduler.api.tree.task import Task
from scheduler.api.tree.task_category import TaskCategory

from .._base_manager import BaseManager, require_class


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

    @require_class(BaseTreeItem, raise_error=True)
    def is_task(self, item):
        """Check if tree item is task.

        Args:
            item (BaseTreeItem): tree item to check.

        Return:
            (bool): whether or not item is task.
        """
        return isinstance(item, Task)

    @require_class(BaseTreeItem, raise_error=True)
    def is_task_category(self, item):
        """Check if tree item is task category.

        Args:
            item (BaseTreeItem): tree item to check.

        Return:
            (bool): whether or not item is task category.
        """
        return isinstance(item, TaskCategory)

    @require_class(BaseTreeItem, raise_error=True)
    def is_top_level_task(self, item):
        """Check if tree item is a top level task.

        Args:
            item (BaseTreeItem): tree item to check.

        Return:
            (bool): whether or not item is top level task.
        """
        return isinstance(item, Task) and isinstance(item.parent, TaskCategory)

    @require_class(BaseTreeItem, raise_error=True)
    def is_task_category_or_top_level_task(self, item):
        """Check if tree item is a top level task.

        Args:
            item (BaseTreeItem): tree item to check.

        Return:
            (bool): whether or not item is task category or top level task.
        """
        return (self.is_task_category(item) or self.is_top_level_task(item))
