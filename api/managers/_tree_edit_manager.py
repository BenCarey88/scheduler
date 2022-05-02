"""Tree edit manager for managing edits on tree items."""


from scheduler.api.common.date_time import DateTime
from scheduler.api.edit.tree_edit import (
    InsertChildrenEdit,
    ModifyChildrenEdit,
    MoveChildrenEdit,
    MoveTreeItemEdit,
    RemoveChildrenEdit,
    RenameChildrenEdit,
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

from ._base_managers import BaseTreeManager, class_instance_decorator


class TreeEditManager(BaseTreeManager):
    """Tree edit manager to apply edits to tree items."""
    _task_only = class_instance_decorator(Task, True)
    _task_only_no_error = class_instance_decorator(Task, False)
    _category_only = class_instance_decorator(TaskCategory, True)
    _category_only_no_error = class_instance_decorator(TaskCategory, False)

    def __init__(self, name, user_prefs, tree_root):
        """Initialise class.

        Args:
            name (str): name of tree manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            tree_root (TaskRoot): root task object.
        """
        super(TreeEditManager, self).__init__(name, user_prefs, tree_root)

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

    # TODO: this isn't used. We need a new switch_class edit that replaces this
    def replace_child(self, tree_item, name, new_child):
        """Replace child at given name with new_child.

        Args:
            tree_item (BaseTreeItem): the tree item to edit.
            name (str): name of child item to replace.
            new_child (BaseTreeItem): new tree item to replace the original
                child.

        Raises:
            (ChildNameError): if new_child has different name to old one.
            (MultipleParentsError): if the child has a different tree item as
                a parent.
            (UnallowedChildType): if the child_type is not allowed.
        """
        if name != new_child.name:
            raise ChildNameError(
                "Can't replace child {0} with new child of "
                "different name {1}".format(name, new_child.name)
            )
        if type(new_child) not in tree_item._allowed_child_types:
            raise UnallowedChildType(tree_item.__class__, type(new_child))
        if new_child.parent != tree_item:
            parent_name = new_child.parent.name if new_child.parent else "None"
            raise MultipleParentsError(
                "child {0} has incorrect parent: {1} instead of {2}".format(
                    new_child.name, parent_name, tree_item.name
                )
            )
        ModifyChildrenEdit.create_and_run(
            tree_item,
            {name: new_child},
        )

    def move(self, tree_item, new_index):
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

    def set_name(self, tree_item, new_name):
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
            raise Exception("Cannot rename root tree item")

    @_task_only
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

    @_task_only_no_error
    def change_task_type(self, task_item, new_type):
        """Change task type to new type.

        Args:
            task_item (Task): task to update type of.
            new_type (TaskType): new type to change to.
        """
        if new_type != task_item.type:
            ChangeTaskTypeEdit.create_and_run(task_item, new_type)
