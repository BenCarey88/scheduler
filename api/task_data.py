"""Module for reading and writing task data.

At any one time the scheduler ui should have one TaskData item that is
used across all its tabs and widgets.
"""

from collections import OrderedDict
import json
import os

from api.tree.base_tree_item import BaseTreeItem

from .tree.task import Task
from .tree.task_category import TaskCategory


class TaskFileError(Exception):
    """Exception for when the tasks file is missing or unreadable."""
    pass


class TaskData(object):
    """Object representing all the task data for the scheduler."""

    def __init__(self, _dict, file_path):
        """Initialize TaskData item.

        Args:
            _dict (OrderedDict): dictionary representing the
                task data.
            file_path (str): path to file this should be saved in.
        """
        self._dict = _dict
        self._file_path = file_path
        self._data = []
        self.update_data_from_dict()
        self._root = None

    @classmethod
    def from_file(cls, file_path):
        """Create TaskData object from json file.

        Args:
            file_path (str): path to json file.

        Raises:
            (TaskFileError): if the task file doesn't exist or cannot be read.

        Returns:
            (TaskData): TaskData object populated with json file dict.
        """
        if not os.path.isfile(file_path):
            raise TaskFileError(
                "Tasks file {0} does not exist".format(file_path)
            )
        with open(file_path, "r") as file_:
            file_text = file_.read()
        try:
            tasks_dict = json.loads(file_text, object_pairs_hook=OrderedDict)
        except json.JSONDecodeError:
            raise TaskFileError(
                "Tasks file {0} is incorrectly formatted for json load".format(
                    file_path
                )
            )
        return cls(tasks_dict, file_path)

    def get_tree_root(self):
        """Get root of tree for all tasks and categories in file.

        Returns:
            (BaseTreeItem): base tree item acting as a root of all task
                categories from file.
        """
        if not self._root:
            self._root = BaseTreeItem("Root")
            for task_item in self._data:
                self._root.add_child(task_item)
        return self._root

    def set_file_path(self, file_path):
        """Change file path to read/write from.

        Args:
            file_path (str): new file path.
        """
        self._file_path = file_path

    def update_data_from_dict(self):
        """Update Task/TaskCategory objects from internal dict."""
        self._data = []
        for category_name, category_dict in self._dict.items():
            category = TaskCategory.from_dict(category_dict, category_name)
            self._data.append(category)

    def update_dict_from_data(self):
        """Update dict from Task or TaskCategory data."""
        self._dict = OrderedDict()
        for task_item in self._data:
            self._dict[task_item.name] = task_item.to_dict()

    def write(self):
        """Write data to file"""
        self.update_dict_from_data()
        if not os.path.isdir(os.path.dirname(self._file_path)):
            raise TaskFileError(
                "Tasks file directory {0} does not exist".format(
                    self._file_path
                )
            )
        with open(self._file_path, 'w') as f:
            json.dump(self._dict, f, indent=4)
