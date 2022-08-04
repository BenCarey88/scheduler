"""Root task item.

At any one time the scheduler ui should have one TaskRoot item that is
used across all its tabs and widgets, and one archive TaskRoot.
"""

from scheduler.api.common.object_wrappers import HostedDataDict
from scheduler.api.serialization.serializable import (
    SaveType,
    SerializableFileTypes,
)
from scheduler.api.utils import fallback_value

from .task_category import TaskCategory


class TaskRoot(TaskCategory):
    """Root item for all task data for the scheduler."""
    _SAVE_TYPE = SaveType.DIRECTORY
    _ORDER_FILE = "root{0}".format(SerializableFileTypes.ORDER)
    _MARKER_FILE = _ORDER_FILE

    _SUBDIR_KEY = "categories"
    _SUBDIR_CLASS = TaskCategory
    _FILE_KEY = None

    CATEGORIES_KEY = _SUBDIR_KEY
    ROOT_NAME = ""
    ARCHIVE_ROOT_NAME = "ARCHIVE"

    def __init__(self, name=None, *args, **kwargs):
        """Initialise TaskRoot item.

        Args:
            name (str or None): name. If None, use ROOT_NAME.
            args (tuple): additional args to allow super class classmethod
                to use this init.
            kwargs (dict): additional kwargs to allow super class classmethod
                to use this init.
        """
        name = name or self.ROOT_NAME
        super(TaskRoot, self).__init__(name=name, parent=None)
        self._allowed_child_types = [TaskCategory]
        self._history_data = None
        self._archive_root = None

    @property
    def _categories(self):
        """Get children that are categories (which should be all children).

        Returns:
            (OrderedDict): dictionary of category children.
        """
        return self._children

    @property
    def archive_root(self):
        """Get corresponding archive tree root for this tree.

        Returns:
            (TaskRoot): archive root.
        """
        return self._archive_root

    def set_archive_root(self, archive_root):
        """Set corresponding archive tree root for this tree.

        Args:
            (TaskRoot): archive root.
        """
        self._archive_root = archive_root

    def get_item_at_path(self, path, strict=False, search_archive=False):
        """Get item at given path.

        Args:
            path (list(str) or str): path to item as a list or a string.
            strict (bool): if True, require that root names of path match
                as well.
            search_archive (bool): if True, search archive root as well.

        Returns:
            (BaseTaskItem or None): tree item at given path, if one exists.
        """
        if isinstance(path, str):
            path_list = path.split(self.TREE_PATH_SEPARATOR)
        elif isinstance(path, list):
            path_list = path
        else:
            return None
        if len(path_list) == 0:
            return None
        tree_item = self
        if path_list[0] != self.name:
            if (search_archive 
                    and self.archive_root is not None
                    and path_list[0] == self.ARCHIVE_ROOT_NAME):
                tree_item = self.archive_root
            elif strict:
                return None
        for name in path_list[1:]:
            tree_item = tree_item.get_child(name)
            if not tree_item:
                break
        return tree_item

    def get_shared_ancestor(self, tree_item):
        """Get the closest ancestor to given item that exists in this tree.

        Args:
            tree_item (BaseTreeItem): tree item to check against.

        Returns:
            (BaseTreeItem): shared ancestor.
        """
        ancestor = self
        while tree_item is not None:
            ancestor = self.get_item_at_path(tree_item.path)
            if ancestor is not None:
                return ancestor
            tree_item = tree_item.parent
        return ancestor

    def create_missing_ancestors(self, tree_item, shared_ancestor=None):
        """Create ancestors that are missing to get to given item.

        Args:
            tree_item (BaseTreeItem): tree item to check against.
            shared_ancestor (BaseTreeItem or None): pre-calculated shared
                ancestor; if not given, we work it out here.

        Returns:
            (list(BaseTreeItem)): newly created skeletal ancestors. The
                created ancestors will each contain the next one down
                as a child but no other children. The created items are
                not activated, and will not contain this item in their
                child list.
        """
        missing_ancestors = []
        shared_ancestor = fallback_value(
            shared_ancestor,
            self.get_shared_ancestor(tree_item),
        )
        tree_item = tree_item.parent
        if tree_item is None:
            return []
        while tree_item.path_list[1:] != shared_ancestor.path_list[1:]:
            new_ancestor = tree_item.clone()
            if missing_ancestors:
                child = missing_ancestors[0]
                new_ancestor._children[child.name] = child
            missing_ancestors.insert(0, new_ancestor)
            tree_item = tree_item.parent
        return missing_ancestors

    def get_history_for_date(self, date):
        """Get task history dict at given date.

        Args:
            date (Date): date to query.

        Returns:
            (dict): history dict for given day.
        """
        return self._history_data.get_history_for_date(date)

    @classmethod
    def from_dict(cls, json_dict, name=None):
        """Initialise class from dictionary representation.

        This just overrides the super class implementation by adding in a
        default name.

        Args:
            json_dict (OrderedDict): dictionary representation.
            name (str or None): name of root - if none, use cls.ROOT_NAME.

        Returns:
            (TaskRoot): task root class for given dict.
        """
        name = name or cls.ROOT_NAME
        history_data = HistoryData()
        task_root = super(TaskRoot, cls).from_dict(
            json_dict,
            name=name,
            history_data=history_data,
            parent=None
        )
        task_root._history_data = history_data
        return task_root


# TODO: work out what should happen to history when items are deleted
class HistoryData(object):
    """Struct to store history data for tasks by day, to add to calendar.

    Structure is like this:
    {
        date_1: {
            task_1: {
                status: task_status,
                value: task_value,
                comments: {
                    time_1: comment_1,
                    time_2: comment_2,
                    ...
                }
            },
            ...
        },
        ...
    }

    This is built up when reading the items from dict, and then passed
    to the calendar afterwards.
    """
    def __init__(self):
        """Initialize structure."""
        self._dict = {}

    def _add_data(self, date, task, history_dict):
        """Add history for given tree item at given date.

        Args:
            date (Date): date to add at.
            task (Task): tree item to add history for.
            history_dict (dict): dict representing history for item.
        """
        self._dict.setdefault(date, HostedDataDict())[task] = history_dict

    def get_history_for_date(self, date):
        """Get history at given date.

        Note that this adds a subdict to the internal if one doesn't exist
        so that any edits to this dictionary will be seen in the returned
        dict too.

        Args:
            date (Date): date to add at.

        Returns:
            (dict): history dict for given day.
        """
        return self._dict.setdefault(date, HostedDataDict())

    def _update_for_task(self, date, task):
        """Update dict to get history for task at given date.

        Args:
            date (Date): date to update at.
            task (Task): task to get history for.
        """
        history_dict = task.history.get_dict_at_date(date)
        if history_dict != self._dict.get(date, {}).get(task):
            self._dict.setdefault(date, HostedDataDict())[task] = history_dict
