"""Tree edit manager for managing edits on tree items."""


from types import new_class
from scheduler.api.common.date_time import DateTime
from scheduler.api.edit.tree_edit import (
    InsertChildrenEdit,
    MoveChildrenEdit,
    MoveTreeItemEdit,
    RemoveChildrenEdit,
    RenameChildrenEdit,
    ReplaceTreeItemEdit,
)
from scheduler.api.edit.task_edit import (
    ChangeTaskTypeEdit,
    UpdateTaskHistoryEdit,
)
from scheduler.api.tree.exceptions import (
    ChildNameError,
    MultipleParentsError,
    UnallowedChildType,
)
from scheduler.api.tree.task import Task, TaskStatus, TaskType
from scheduler.api.tree.task_category import TaskCategory
from scheduler.api.tree.task_root import TaskRoot

from ._base_managers import BaseTreeManager, require_class


class TreeEditManager(BaseTreeManager):
    """Tree edit manager to apply edits to tree items."""
    def __init__(self, name, user_prefs, tree_root, archive_tree_root):
        """Initialise class.

        Args:
            name (str): name of tree manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            tree_root (TaskRoot): root task object.
            archive_tree_root (TaskRoot): root archive task object.
        """
        super(TreeEditManager, self).__init__(
            name,
            user_prefs,
            tree_root,
            archive_tree_root,
        )

    def create_child(
            self,
            tree_item,
            name,
            child_type=None,
            index=None,
            **kwargs):
        """Create child item and add to children dict.

        Args:
            tree_item (BaseTreeItem): tree item to edit.
            name (str): name of child.
            child_type (class or None): class to use for child init. If None,
                use current class.
            index (int or None): if given, insert child at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to child init.

        Raises:
            (UnallowedChildType): if the child_type is not allowed.
            (IndexError): if the given index is out of range of the child dict.

        Returns None if:
            - a child with the given name already exists.

        Returns:
            (BaseTreeItem or None): newly created child, if successful.
        """
        if name in tree_item._children:
            return None
        child_type = child_type or tree_item.__class__
        if child_type not in tree_item._allowed_child_types:
            raise UnallowedChildType(tree_item.__class__, child_type)
        child = child_type(name, parent=tree_item, **kwargs)
        if index is None:
            index = len(tree_item._children)
        if index < 0 or index > len(tree_item._children):
            raise IndexError("Index given is larger than number of children.")
        InsertChildrenEdit.create_and_run(
            tree_item,
            {name: (index, child)},
        )
        return child

    def create_new_child(
            self,
            tree_item,
            default_name="child",
            child_type=None,
            index=None,
            **kwargs):
        """Create a new child with a default name.

        This adds a number at the end of the name to allow us to add mutliple
        new children with different names.

        Args:
            tree_item (BaseTreeItem): the tree item to edit.
            default_name (str): the default name to use (before appending the
                number).
            child_type (class or None): class to use for child init. If None,
                use current class.
            index (int or None): if given, insert child at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to child init.

        Returns:
            (BaseTreeItem): newly created child.
        """
        suffix = 1
        name = default_name + str(suffix).zfill(3)
        while name in tree_item._children.keys():
            suffix += 1
            name = default_name + str(suffix).zfill(3)
        return self.create_child(
            tree_item,
            name,
            child_type,
            index=index,
            **kwargs
        )

    def create_new_subtask(
            self,
            tree_item,
            default_name="task",
            index=None,
            **kwargs):
        """Create a new task child.

        This adds a number at the end of the name to allow us to add mutliple
        new children with different names.

        Args:
            tree_item (Task or TaskCategory): the tree item to edit.
            default_name (str): the default name to use (before appending the
                number).
            index (int or None): if given, insert child at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to child init.

        Returns:
            (TaskCategory): newly created child.
        """
        return self.create_new_child(
            tree_item,
            default_name,
            Task,
            index,
            **kwargs,
        )

    @require_class(TaskCategory, raise_error=False)
    def create_new_subcategory(
            self,
            tree_item,
            default_name="category",
            index=None,
            **kwargs):
        """Create a new category child.

        This adds a number at the end of the name to allow us to add mutliple
        new children with different names.

        Args:
            tree_item (TaskCategory): the tree item to edit.
            default_name (str): the default name to use (before appending the
                number).
            index (int or None): if given, insert child at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to child init.

        Returns:
            (TaskCategory): newly created child.
        """
        return self.create_new_child(
            tree_item,
            default_name,
            TaskCategory,
            index,
            **kwargs,
        )

    def create_sibling(self, tree_item, name, index=None, **kwargs):
        """Create sibling item for tree item.

        Args:
            tree_item (BaseTreeItem): the tree item to edit.
            name (str): the name of the sibling.
            index (int or None): if given, insert sibling at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to sibling init.

        Returns:
            (BaseTreeItem or None): newly created sibling, if one could be
                created, else None.
        """
        if not tree_item.parent:
            return None
        return self.create_child(
            tree_item.parent,
            name,
            child_type=tree_item.__class__,
            index=index,
            **kwargs
        )

    def create_new_sibling(
            self,
            tree_item,
            default_name="sibling",
            index=None,
            **kwargs):
        """Create sibling item for tree item.

        Args:
            tree_item (BaseTreeItem): the tree item to edit.
            default_name (str): the default name to use (before appending
                the number).
            index (int or None): if given, insert sibling at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to sibling init.

        Returns:
            (BaseTreeItem or None): newly created sibling, if one could be
                created, else None. In subclasses, this will use the type
                of the subclass.
        """
        if not tree_item.parent:
            return None
        return self.create_new_child(
            tree_item.parent,
            default_name,
            child_type=tree_item.__class__,
            index=index,
            **kwargs
        )

    def remove_child(self, tree_item, name):
        """Remove an existing child from this item's children dict.

        Args:
            tree_item (BaseTreeItem): the tree item to edit.
            name (str): name of child item to remove.
        """
        if name in tree_item._children.keys():
            RemoveChildrenEdit.create_and_run(
                tree_item,
                [name],
            )

    def remove_children(self, tree_item, names):
        """Remove existing children from this item's children dict.

        Args:
            tree_item (BaseTreeItem): the tree item to edit.
            name (list(str)): name of child items to remove.
        """
        names = [name for name in names if name in tree_item._children.keys()]
        RemoveChildrenEdit.create_and_run(
            tree_item,
            names,
        )

    def set_item_name(self, tree_item, new_name):
        """Set item name.

        This setter also updates the item's name in its parent's child dict.

        Args:
            tree_item (BaseTreeItem): the tree item to edit.
            new_name (str): new item name.
        """
        parent = tree_item.parent
        if parent:
            if parent.get_child(new_name):
                return None
            RenameChildrenEdit.create_and_run(
                parent,
                {tree_item.name: new_name},
            )
        else:
            # TODO: sort these exceptions
            raise Exception("Cannot rename root tree item")

    def move_item_local(self, tree_item, new_index):
        """Move tree item to new index in parent's _children dict.

        Args:
            tree_item (BaseTreeItem): the tree item to edit.
            new_index (int): new index to move to.
        """
        if not tree_item.parent:
            return
        if new_index >= tree_item.parent.num_children() or new_index < 0:
            return
        if new_index == tree_item.index():
            return
        MoveChildrenEdit.create_and_run(
            tree_item.parent,
            {tree_item.name: new_index},
        )

    def move_item_by_path(
            self,
            path_to_item,
            path_to_new_parent,
            index=None):
        """Move item at given path under parent at given path.

        Args:
            path_to_item (list(str) or str): path of item to move.
            path_to_new_parent (list(str) or str): path of parent to move it
                to.
            index (int or None): index in new parent's _children dict to move
                it to. If None, add at end.
        """
        item = self._tree_root.get_item_at_path(path_to_item)
        new_parent = self._tree_root.get_item_at_path(path_to_new_parent)
        if not item or not new_parent or item.is_ancestor(new_parent):
            return
        if index is None:
            index = new_parent.num_children()
        if (item.parent != new_parent
                and item.name in new_parent._children.keys()):
            return
        if type(item) not in new_parent._allowed_child_types:
            return
        if index < 0 or index > new_parent.num_children():
            return
        MoveTreeItemEdit.create_and_run(
            item,
            new_parent,
            index,
        )

    def change_item_class(self, tree_item):
        """Toggle item class between Task and TaskCategory.

        Args:
            tree_item (BaseTreeItem): the tree item to edit.
        """
        if tree_item.parent is None:
            raise Exception("Cannot change item class for root tree item")
        if isinstance(tree_item, Task):
            new_class = TaskCategory
        elif isinstance(tree_item, TaskCategory):
            new_class = Task
        else:
            raise Exception(
                "Cannot change item class for tree item of type {0}".format(
                    tree_item.__class__.__name__
                )
            )
        new_tree_item = new_class(tree_item.name)
        ReplaceTreeItemEdit.create_and_run(tree_item, new_tree_item)

    @require_class(Task, raise_error=True)
    def update_task(
            self,
            task_item,
            status=None,
            date_time=None,
            comment=None):
        """Update task history and status.

        Args:
            task_item (Task): task item to edit.
            status (TaskStatus or None): status to update task with. If None
                given, we calculate the next one.
            date (DateTime or None): datetime object to update task history
                with.
            comment (str): comment to add to history if needed.
        """
        if status is None:
            current_status = task_item.status
            if current_status == TaskStatus.UNSTARTED:
                if task_item.type == TaskType.ROUTINE:
                    status = TaskStatus.COMPLETE
                else:
                    status = TaskStatus.IN_PROGRESS
            elif current_status == TaskStatus.IN_PROGRESS:
                status = TaskStatus.COMPLETE
            elif current_status == TaskStatus.COMPLETE:
                status = TaskStatus.UNSTARTED

        if date_time is None:
            date_time = DateTime.now()
        UpdateTaskHistoryEdit.create_and_run(
            task_item,
            date_time,
            status,
            comment=comment,
        )

    @require_class(Task, raise_error=False)
    def change_task_type(self, task_item, new_type):
        """Change task type to new type.

        Args:
            task_item (Task): task to update type of.
            new_type (TaskType): new type to change to.
        """
        if new_type != task_item.type:
            ChangeTaskTypeEdit.create_and_run(task_item, new_type)
