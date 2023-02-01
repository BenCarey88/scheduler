"""Base tree manager class."""

from scheduler.api.tree.base_task_item import BaseTaskItem
from scheduler.api.tree.task import Task
from scheduler.api.tree.task_category import TaskCategory

from .._base_manager import BaseManager, require_class


class BaseTreeManager(BaseManager):
    """Base tree manager class to build tree manager classes from."""
    def __init__(self, name, user_prefs, tree_root, filterer):
        """Initialize class.

        Args:
            name (str): name of tree manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            tree_root (TaskRoot): root task object.
            filterer (Filterer): filterer class for storing filters.
        """
        self._tree_root = tree_root
        self._archive_tree_root = tree_root.archive_root
        super(BaseTreeManager, self).__init__(
            user_prefs,
            filterer=filterer,
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

    def iter_tree(self, include_root=False):
        """Iterate through all tree items.

        Args:
            include_root (bool): if True, include root in iteration.

        Yields:
            (BaseTaskItem): each item in tree, from top down.
        """
        if include_root:
            yield self._tree_root
        for descendant in self._tree_root.iter_descendants:
            yield descendant

    @require_class(BaseTaskItem, raise_error=True)
    def is_top_level_task(self, item):
        """Check if tree item is a top level task.

        Args:
            item (BaseTaskItem): tree item to check.

        Return:
            (bool): whether or not item is top level task.
        """
        return isinstance(item, Task) and isinstance(item.parent, TaskCategory)

    @require_class(BaseTaskItem, raise_error=True)
    def is_task_category_or_top_level_task(self, item):
        """Check if tree item is a top level task.

        Args:
            item (BaseTaskItem): tree item to check.

        Return:
            (bool): whether or not item is task category or top level task.
        """
        return (self.is_task_category(item) or self.is_top_level_task(item))

    @require_class((Task, TaskCategory), raise_error=True)
    def get_task_category_or_top_level_task(self, item):
        """Get task category or top level task ancestor of item.

        Args:
            item (BaseTaskItem): tree item to use.

        Return:
            (Task or TaskCategory or None): task category or top level task
                of item, if found.
        """
        if self.is_task_category_or_top_level_task(item):
            return item
        if item.parent is None:
            return None
        return self.get_task_category_or_top_level_task(item.parent)

    @require_class(BaseTaskItem, raise_error=True)
    def can_accept_child(self, parent_item, child_item):
        """Check if tree item can accept given item as a child.

        An item can be dropped UNLESS one of the following is true:
        - The item is an ancestor of the new parent
        - The parent has a child that is not the item but has the item's name
        - the item is not in the parent's allowed children.

        Args:
            parent_item (BaseTaskItem): parent item to check.
            child_item (BaseTaskItem): child item to check if can be accepted.

        Return:
            (bool): whether or not parent item can accept child item.
        """
        if child_item.is_ancestor(parent_item):
            return False
        if (parent_item != child_item.parent
                and child_item.name in parent_item._children.keys()):
            return False
        if type(child_item) not in parent_item._allowed_child_types:
            return False
        return True
