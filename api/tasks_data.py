"""Module for reading and writing task data."""

from collections import OrderedDict
import json
import os

from .task import Task


class TaskFileError(Exception):
    """Exception for when the tasks file is missing or unreadable."""
    pass


class TaskData(object):
    """Class for reading and writing task data."""

    def __init__(self, tasks_dict, file_path):
        """Initialize TaskData item.

        Args:
            tasks_dict (OrderedDict): dictionary representing the
                task data.
            file_path (str): path to file this should be saved in.
        """
        self._tasks_dict = tasks_dict
        self._file_path = file_path
        self._tasks_data = []
        self.update_tasks_from_dict()

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

    def get_tasks(self):
        """Get all tasks.

        Returns:
            (list(Task)): list of Tasks items.
        """
        return self._tasks_data

    def set_file_path(self, file_path):
        """Change file path to read/write from.

        Args:
            file_path (str): new file path.
        """
        self._file_path = file_path

    def update_tasks_from_dict(self):
        """Update Task objects from internal dict"""
        self._tasks_data = []
        for task_name, task_dict in self._tasks_dict.items():
            task = Task.from_dict(task_dict, task_name)
            self._tasks_data.append(task)

    def update_dict_from_tasks(self):
        """Update tasks dict from Task data."""
        self._tasks_dict = OrderedDict()
        for task in self._tasks_data:
            self._tasks_dict[task.name] = task.to_dict()

    def write(self):
        """Write data to file"""
        self.update_dict_from_tasks()
        if not os.path.isdir(os.path.dirname(self._file_path)):
            raise TaskFileError(
                "Tasks file directory {0} does not exist".format(
                    self._file_path
                )
            )
        with open(self._file_path, 'w') as f:
            json.dump(self._tasks_dict, f, indent=4)
