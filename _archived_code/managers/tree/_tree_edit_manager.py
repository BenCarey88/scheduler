"""Tree edit manager for managing edits on tree items."""

from scheduler.api.common.date_time import Date, DateTime
from scheduler.api.enums import ItemStatus
from scheduler.api.edit.tree_edit import (
    ArchiveTreeItemEdit,
    InsertChildrenEdit,
    MoveChildrenEdit,
    MoveTreeItemEdit,
    RemoveChildrenEdit,
    RenameChildrenEdit,
    ReplaceTreeItemEdit,
)
from scheduler.api.edit.task_edit import (
    ClearTaskHistoryEdit,
    ModifyTaskEdit,
    TrackTaskEdit,
    UntrackTaskEdit,
    UpdateTaskHistoryEdit,
)
from scheduler.api.tree.exceptions import UnallowedChildType
from scheduler.api.tree.task import Task, TaskType
from scheduler.api.tree.task_category import TaskCategory
from scheduler.api.tree.base_task_item import BaseTaskItem

from .._base_manager import require_class
from ._base_tree_manager import BaseTreeManager


class TreeEditManager(BaseTreeManager):
    """Tree edit manager to apply edits to tree items."""
    def __init__(self, name, user_prefs, tree_root, filterer, tracker):
        """Initialise class.

        Args:
            name (str): name of tree manager.
            user_prefs (ProjectUserPrefs): project user prefs class.
            tree_root (TaskRoot): root task object.
            filterer (Filterer): filterer class for storing filters.
            tracker (Tracker): tracker to track tasks with.
        """
        super(TreeEditManager, self).__init__(
            name,
            user_prefs,
            tree_root,
            filterer,
            tracker,
        )

    @require_class(BaseTaskItem, raise_error=True)
    def create_child(
            self,
            tree_item,
            name,
            child_type=None,
            index=None,
            **kwargs):
        """Create child item and add to children dict.

        Args:
            tree_item (BaseTaskItem): tree item to edit.
            name (str): name of child.
            child_type (class or None): class to use for child init. If None,
                use current class.
            index (int or None): if given, insert child at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to child init.

        Raises:
            (UnallowedChildType): if the child_type is not allowed.
            (IndexError): if the given index is out of range of the child dict.

        Edit unsuccessful if:
            - a child with the given name already exists.

        Returns:
            (bool): whether or not edit was successful.
        """
        if name in tree_item._children:
            return False
        child_type = child_type or tree_item.__class__
        if child_type not in tree_item._allowed_child_types:
            raise UnallowedChildType(tree_item.__class__, child_type)
        child = child_type(name, parent=tree_item, **kwargs)
        if index is None:
            index = len(tree_item._children)
        if index < 0 or index > len(tree_item._children):
            raise IndexError("Index given is larger than number of children.")
        return InsertChildrenEdit.create_and_run(
            tree_item,
            {name: (index, child)},
        )

    @require_class(BaseTaskItem, raise_error=True)
    def create_new_child(
            self,
            tree_item,
            default_name=None,
            child_type=None,
            index=None,
            **kwargs):
        """Create a new child with a default name.

        This adds a number at the end of the name to allow us to add mutliple
        new children with different names.

        Args:
            tree_item (BaseTaskItem): the tree item to edit.
            default_name (str or None): the default name to use (before
                appending the number). If None, get from class.
            child_type (class or None): class to use for child init. If None,
                use current class.
            index (int or None): if given, insert child at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to child init.

        Returns:
            (bool): whether or not edit was successful.
        """
        child_type = child_type or tree_item.__class__
        default_name = default_name or child_type.DEFAULT_NAME
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

    @require_class((Task, TaskCategory), raise_error=True)
    def create_new_subtask(
            self,
            tree_item,
            default_name=None,
            index=None,
            **kwargs):
        """Create a new task child.

        This adds a number at the end of the name to allow us to add mutliple
        new children with different names.

        Args:
            tree_item (Task or TaskCategory): the tree item to edit.
            default_name (str or None): the default name to use (before
                appending the number).
            index (int or None): if given, insert child at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to child init.

        Returns:
            (bool): whether or not edit was successful.
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
            default_name=None,
            index=None,
            **kwargs):
        """Create a new category child.

        This adds a number at the end of the name to allow us to add mutliple
        new children with different names.

        Args:
            tree_item (TaskCategory): the tree item to edit.
            default_name (str or None): the default name to use (before
                appending the number). If None, get from class.
            index (int or None): if given, insert child at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to child init.

        Returns:
            (bool): whether or not edit was successful.
        """
        return self.create_new_child(
            tree_item,
            default_name,
            TaskCategory,
            index,
            **kwargs,
        )

    @require_class(BaseTaskItem, raise_error=True)
    def create_sibling(self, tree_item, name, index=None, **kwargs):
        """Create sibling item for tree item.

        Args:
            tree_item (BaseTaskItem): the tree item to edit.
            name (str): the name of the sibling.
            index (int or None): if given, insert sibling at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to sibling init.

        Returns:
            (bool): whether or not edit was successful.
        """
        if not tree_item.parent:
            return False
        return self.create_child(
            tree_item.parent,
            name,
            child_type=tree_item.__class__,
            index=index,
            **kwargs
        )

    @require_class(BaseTaskItem, raise_error=True)
    def create_new_sibling(
            self,
            tree_item,
            default_name=None,
            index=None,
            **kwargs):
        """Create sibling item for tree item.

        Args:
            tree_item (BaseTaskItem): the tree item to edit.
            default_name (str or None): the default name to use (before
                appending the number). If None, get from class.
            index (int or None): if given, insert sibling at given index, else
                add at end of _children dict.
            **kwargs: kwargs to be passed to sibling init.

        Returns:
            (bool): whether or not edit was successful.
        """
        if not tree_item.parent:
            return False
        return self.create_new_child(
            tree_item.parent,
            default_name,
            child_type=tree_item.__class__,
            index=index,
            **kwargs
        )

    @require_class(BaseTaskItem, raise_error=True)
    def remove_item(self, tree_item, stack=False):
        """Remove an existing tree item from its parent's children dict.

        Args:
            tree_item (BaseTaskItem): the tree item to remove.
            stack (bool): if True, stack this with the previous edit.

        Returns:
            (bool): whether or not edit was successful.
        """
        parent = tree_item.parent
        if not parent:
            return False
        return RemoveChildrenEdit.create_and_run(
            parent,
            [tree_item.name],
            stack=stack,
        )

    def remove_items(self, tree_items):
        """Remove an existing tree item from its parent's children dict.

        Args:
            tree_items (list(BaseTaskItem)): the tree items to remove.

        Returns:
            (bool): whether or not edit was successful (ie. at least one item
                was removed).
        """
        success = False
        for tree_item in tree_items:
            success = self.remove_item(tree_item, stack=success) or success
        return success

    @require_class((Task, TaskCategory), raise_error=True)
    def set_item_name(self, tree_item, new_name):
        """Set item name.

        This setter also updates the item's name in its parent's child dict.

        Args:
            tree_item (BaseTaskItem): the tree item to edit.
            new_name (str): new item name.

        Returns:
            (bool): whether or not name was successfully set.
        """
        parent = tree_item.parent
        if parent is None:
            return False
        if parent.get_child(new_name):
            return False
        return RenameChildrenEdit.create_and_run(
            parent,
            {tree_item.name: new_name},
        )

    @require_class(BaseTaskItem, raise_error=True)
    def move_item_local(self, tree_item, new_index):
        """Move tree item to new index in parent's _children dict.

        Args:
            tree_item (BaseTaskItem): the tree item to edit.
            new_index (int): new index to move to.

        Returns:
            (bool): whether or not edit was successful.
        """
        if not tree_item.parent:
            return False
        if new_index >= tree_item.parent.num_children() or new_index < 0:
            return False
        old_index = tree_item.index()
        if new_index == old_index:
            return False
        return MoveChildrenEdit.create_and_run(
            tree_item.parent,
            {tree_item.name: new_index},
        )

    @require_class(BaseTaskItem, raise_error=True)
    def move_item(self, item, new_parent, index=None):
        """Move item at given path under parent at given path.

        Args:
            item (BaseTaskItem): item to move.
            new_parent (BaseTaskItem): parent to move it to.
            index (int or None): index in new parent's _children dict to move
                it to. If None, add at end.

        Returns:
            (bool): whether or not edit was successful.
        """
        if not self.can_accept_child(new_parent, item):
            return False
        if index is None:
            index = new_parent.num_children()
        if index < 0 or index > new_parent.num_children():
            return False
        return MoveTreeItemEdit.create_and_run(
            item,
            new_parent,
            index,
        )

    @require_class(BaseTaskItem, raise_error=True)
    def change_item_class(self, tree_item):
        """Toggle item class between Task and TaskCategory.

        Args:
            tree_item (BaseTaskItem): the tree item to edit.

        Returns:
            (bool): whether or not edit was successful.
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
        return ReplaceTreeItemEdit.create_and_run(tree_item, new_tree_item)

    @require_class(Task, raise_error=False)
    def update_task(
            self,
            task_item,
            date_time=None,
            status=None,
            value=None,
            status_override=None,
            comment=None,
            remove_from_prev_time=True,
            ignore_time=False):
        """Update task history and status.

        Args:
            task_item (Task): task item to edit.
            date_time (Date, DateTime or None): date or datetime to update
                task history with. If None, we use current date and time.
            time (Time or None): time to update task history with, if used.
            status (ItemStatus or None): status to update task with. If None
                given, we calculate the next one.
            value (variant or None): value to set for task at given time. If
                None, we ignore.
            status_override (bool or None): if True, this sets the status as
                an override, so it's used even if it's less complete than
                earlier statuses.
            comment (str): comment to add to history if needed.
            remove_from_prev_time (bool): if True, remove task from previous
                times on same day to avoid clogging up.
            ignore_time (bool): only used if no date_time arg is given. In
                this case, if True, we update at the current date, otherwise
                we update at the current date and time.

        Returns:
            (bool): whether or not edit was successful.
        """
        if date_time is None:
            if ignore_time:
                date_time = Date.now()
            else:
                date_time = DateTime.now()

        if isinstance(date_time, DateTime):
            date = date_time.date()
        elif isinstance(date_time, Date):
            date = date_time
        else:
            raise Exception(
                "date_time must be Date or DateTime, not {0}".format(date_time)
            )

        if status is None:
            current_status = task_item.get_status_at_date(date)
            if current_status == ItemStatus.UNSTARTED:
                if task_item.type == TaskType.ROUTINE:
                    status = ItemStatus.COMPLETE
                else:
                    status = ItemStatus.IN_PROGRESS
            elif current_status == ItemStatus.IN_PROGRESS:
                status = ItemStatus.COMPLETE
            elif current_status == ItemStatus.COMPLETE:
                status = ItemStatus.UNSTARTED

        # remove task from previous time on same day to avoid clogging up
        old_datetime = None
        if remove_from_prev_time and isinstance(date_time, DateTime):
            history = task_item.history
            old_time = history.find_influencer_at_date(date, task_item)
            if old_time is not None:
                old_datetime = DateTime.from_date_and_time(date, old_time)
        return UpdateTaskHistoryEdit.create_and_run(
            task_item=task_item,
            influencer=task_item,
            old_datetime=old_datetime,
            new_datetime=date_time,
            new_status=status,
            new_value=value,
            new_status_override=status_override,
        )

    @require_class(Task, raise_error=False)
    def clear_task_history(self, task_item):
        """Clear task history.

        Args:
            task_item (Task): task item to edit.

        Returns:
            (bool): whether or not edit was successful.
        """
        return ClearTaskHistoryEdit.create_and_run(task_item)

    @require_class(Task, raise_error=False)
    def change_task_type(self, task_item, new_type=None):
        """Change task type to new type.

        Args:
            task_item (Task): task to update type of.
            new_type (TaskType or None): new type to change to. If None,
                we just toggle.

        Returns:
            (bool): whether or not edit was successful.
        """
        if new_type is None:
            new_type = (
                TaskType.ROUTINE if task_item.type == TaskType.GENERAL
                else TaskType.GENERAL
            )
        if new_type == task_item.type:
            return False
        return ModifyTaskEdit.create_and_run(
            task_item,
            {task_item._type: new_type},
        )

    @require_class(BaseTaskItem, raise_error=False)
    def modify_task_item(
            self,
            task_item,
            name=None,
            display_name=None,
            type=None,
            size=None,
            importance=None,
            stack=False):
        """Modify attributes of task.

        Args:
            name (str)
            task_item (Task): task to modify.
            name (str or None): new name to change to, if given.
            display_name (str or None): new display name to change to, if
                given.
            type (TaskType or None): new task type, if given.
            size (ItemSize or None): new size to change to, if given.
            importance (ItemImportance): new importance, if given.
            stack (bool): if True, stack this with the previous edit.

        Returns:
            (bool): whether or not edit was successful.
        """
        is_task = self.is_task(task_item)
        attr_dict = {
            task_item._name: name,
            task_item._display_name: display_name,
        }
        if is_task:
            attr_dict.update({
                task_item._type: type,
                task_item._size: size,
                task_item._importance: importance,
            })
        attr_dict = {
            attr: value
            for attr, value in attr_dict.items() if value is not None
        }
        return ModifyTaskEdit.create_and_run(
            task_item,
            attr_dict,
            is_task=is_task,
            stack=stack,
        )

    @require_class(BaseTaskItem, raise_error=False)
    def archive_item(
            self,
            tree_item,
            rename="",
            merge=True,
            override=True,
            recursive=True):
        """Archive tree item.

            tree_item (BaseTreeItem): item to archive.
            archive_root (BaseTreeItem): root of archive tree.
            rename (str): if given, rename the item to this if it already
                exists in the archive. This cannot be given if merge is True.
            merge (bool): if True, and item already exists in archive tree,
                merge this one into it. Otherwise, we rename the item we're
                archiving. This cannot be True if rename arg is given.
            override (bool): if True, keep attributes of the source item when
                merging, otherwise keep those of the dest item. If renaming,
                override=True tells us that the original archived item should
                be renamed rather than the newly archived item.
            recursive (bool): if True, run any merges recursively for children
                of the item that already exist in the archive tree.

        Returns:
            (bool): whether or not edit was successful.
        """
        return ArchiveTreeItemEdit.create_and_run(
            tree_item,
            self.archive_tree_root,
            rename=rename,
            merge=merge,
            override=override,
            recursive=recursive,
        )

    @require_class(Task, raise_error=False)
    def toggle_task_tracking(self, task_item):
        """Add/remove task item to/from tracker.

        Args:
            task_item (Task): task item to add/remove.

        Returns:
            (bool): whether or not edit was successful.
        """
        if task_item.is_tracked:
            return UntrackTaskEdit.create_and_run(task_item, self._tracker)
        return TrackTaskEdit.create_and_run(task_item, self._tracker)
