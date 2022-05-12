"""Root task item.

At any one time the scheduler ui should have one TaskRoot item that is
used across all its tabs and widgets.
"""

from collections import OrderedDict

from scheduler.api.edit.tree_edit import MoveTreeItemEdit
from scheduler.api.serialization.serializable import (
    SaveType,
    SerializationError,
    SerializableFileTypes,
)

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

    def __init__(self, directory_path=None, name=None, *args, **kwargs):
        """Initialise TaskRoot item.

        Args:
            directory_path (str or None): path to directory this should be
                saved to, or None if not set yet.
            name (str or None): name. If None, use ROOT_NAME.
            args (tuple): additional args to allow super class classmethod
                to use this init.
            kwargs (dict): additional kwargs to allow super class classmethod
                to use this init.
        """
        name = name or self.ROOT_NAME
        super(TaskRoot, self).__init__(name=name, parent=None)
        self._directory_path = directory_path
        self._allowed_child_types = [TaskCategory]
        self._history_data = None

        # use category in place of subcategory in category function names
        # self.create_category = self.create_subcategory
        # self.create_new_category = self.create_subcategory
        # self.add_category = self.add_subcategory
        # self.remove_category = self.remove_subcategory
        # self.remove_categories = self.remove_subcategories
        # self.get_category = self.get_subcategory
        # self.get_category_at_index = self.get_subcategory_at_index
        # self.get_all_categories = self.get_all_subcategories
        # self.num_categories = self.num_subcategories
        # self.num_category_descendants = self.num_subcategory_descendants

    @property
    def _categories(self):
        """Get children that are categories (which should be all children).

        Returns:
            (OrderedDict): dictionary of category children.
        """
        return self._children

    def get_item_at_path(self, path):
        """Get item at given path.

        Args:
            path (list(str) or str): path to item as a list or a string.

        Returns:
            (BaseTreeItem or None): tree item at given path, if one exists.
        """
        if isinstance(path, str):
            path_list = path.split(self.TREE_PATH_SEPARATOR)
        elif isinstance(path, list):
            path_list = path
        else:
            return
        if len(path_list) == 0:
            return None
        if path_list[0] != self.name:
            return None
        tree_item = self
        for name in path_list[1:]:
            tree_item = tree_item.get_child(name)
            if not tree_item:
                break
        return tree_item

    # TODO: does this belong here? Potentially yeah, arguably it's quite
    # good for tree root to have a lot of control of the tree, then tree
    # manager could use functions from there to control stuff
    # there's just a bit of an open q surrounding what should be used to edit
    # a tree as currently it's done by edits, within each tree class, by tree
    # manager and directly from both model and widgets.
    # current ideal is:
    #     widget -> (model) -> tree_manager -> tree_items -> edits
    # but gets messy bc widgets still need to have access to tree items
    # directly, for TaskWdigets and CategoryWidgets if nothing else
    #  SEE DOC IN NOTES FOR DISCUSSION ON THIS.
    #
    # TODO: maybe build up an open qs/to-do list page rather than scattering
    # unneat todo questions around lol - I think the in-code TODOs should be
    # reserved for things we definitely want to implement
    # def move_tree_item(self, path_to_item, path_to_new_parent, index=None):
    #     """Move item at given path under parent at given path.

    #     Args:
    #         path_to_item (list(str) or str): path list of item to move.
    #         path_to_new_parent (list(str) or str): path list of parent to move it to.
    #         index (int or None): index in new parent's _children dict to move
    #             it to. If None, add at end.
    #     """
    #     item = self.get_item_at_path(path_to_item)
    #     new_parent = self.get_item_at_path(path_to_new_parent)
    #     if not item or not new_parent or item.is_ancestor(new_parent):
    #         return
    #     if index is None:
    #         index = new_parent.num_children()
    #     if (item.parent.id != new_parent.id
    #             and item.name in new_parent._children.keys()):
    #         return
    #     if type(item) not in new_parent._allowed_child_types:
    #         return
    #     if index < 0 or index > new_parent.num_children():
    #         return
    #     MoveTreeItemEdit.create_and_run(
    #         item,
    #         new_parent,
    #         index,
    #         register_edit=self._register_edits,
    #     )

    def get_history_for_date(self, date):
        """Get task history dict at given date.

        Args:
            date (Date): date to add at.

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


class HistoryData(object):
    """Struct to store history data for tasks by day, to add to calendar.

    This is built up when reading the items from dict, and then passed
    to the calendar afterwards.
    """
    def __init__(self):
        """Initialize structure."""
        self._dict = {}

    def add_data(self, date, task, history_dict):
        """Add history for given tree item at given date.

        Args:
            date (Date): date to add at.
            task (Task): tree item to add history for.
            history_dict (dict): dict representing history for item.
        """
        self._dict.setdefault(date, {})[task] = history_dict

    def get_history_for_date(self, date):
        """Get history at given date.

        Args:
            date (Date): date to add at.

        Returns:
            (dict): history dict for given day.
        """
        return self._dict.get(date, {})
