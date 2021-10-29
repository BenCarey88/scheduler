"""Task class."""

from collections import OrderedDict
from functools import partial
import json
import os

from .base_tree_item import BaseTreeItem
from .exceptions import TaskFileError


class TaskType():
    """Enumeration for task types."""
    ROUTINE = "Routine"
    GENERAL = "General"


class TaskStatus():
    """Enumeration for task statuses."""
    UNSTARTED = "Unstarted"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"


class Task(BaseTreeItem):
    """Class representing a generic task."""

    def __init__(
            self,
            name,
            parent=None,
            task_type=None,
            status=None,
            history=None):
        """Initialise task class.

        Args:
            name (str): name of task.
            parent (Task or None): parent of current task, if task is subtask.
            task_type (TaskType or None): type of task (routine or general).
                if None, we default to general.
            status (TaskStatus or None): status of current task. If None,
                we default to unstarted.
            history (TaskHistory or None): task history, if exists.
        """
        super(Task, self).__init__(name, parent)
        self.type = task_type or TaskType.GENERAL
        self.status = status or TaskStatus.UNSTARTED
        self.history = history or TaskHistory(self)

        # new attribute and method names for convenience
        self.create_subtask = self.create_child
        self.create_new_subtask = partial(
            self.create_new_child,
            default_name="subtask"
        )
        self.add_subtask = self.add_child
        self.create_sibling_task = self.create_sibling
        self.create_new_sibling_task = partial(
            self.create_new_sibling,
            default_name = "task"
        )
        self.add_sibling_task = self.add_sibling
        self.remove_subtask = self.remove_child
        self.remove_subtasks = self.remove_children
        self.get_subtask = self.get_child
        self.get_subtask_at_index = self.get_child_at_index
        self.get_all_subtasks = self.get_all_children
        self.num_subtasks = self.num_children
        self.num_subtask_descendants = self.num_descendants

    @property
    def _subtasks(self):
        """Get subtasks dict.

        This is identical to children dict. It is implemented as a property so
        that it stays updated with the _children dict.

        Returns:
            (OrderedDict): dictionary of subtasks.
        """
        return self._children

    def update_task(self, date_time, status, comment=None):
        """Update task history and status.

        Args:
            date (datetime.datetime): datetime object to update task with.
            status (TaskStatus): status to update task with.
            comment (str): comment to add to history if needed.
        """
        self.status = status
        self.history.update(date_time, status, comment)

    def to_dict(self):
        """Get json compatible dictionary representation of class.

        The structure  is:
        {
            status: task_status,
            type: task_type,
            history: task_history_dict,
            subtasks: {
                subtask1_name: subtask1_dict,
                subtask2_name: subtask2_dict,
                ...
            }
        }
        Note that this does not contain a name field, as the name is expected
        to be added as a key to this dictionary in the tasks json files.

        Returns:
            (OrderedDict): dictionary representation.
        """
        json_dict = {
            "status": self.status,
            "type": self.type,
        }
        if self.history:
            json_dict["history"] = self.history.dict
        if self._subtasks:
            subtasks_dict = OrderedDict()
            for subtask_name, subtask in self._subtasks.items():
                subtasks_dict[subtask_name] = subtask.to_dict()
            json_dict["subtasks"] = subtasks_dict
        return json_dict

    @classmethod
    def from_dict(cls, json_dict, name, parent=None):
        """Initialise class from dictionary representation.

        The json_dict is expected to be structured as described in the to_dict
        docstring.

        Args:
            json_dict (OrderedDict): dictionary representation.
            name (str): name of task.
            parent (Task, TaskCategory or None): parent of task.

        Returns:
            (Task): task class for given dict.
        """
        task_type = json_dict.get("type", None)
        task_status = json_dict.get("status", None)
        task_history = json_dict.get("history", None)
        task = cls(name, parent, task_type, task_status, task_history)

        subtasks = json_dict.get("subtasks", {})
        for subtask_name, subtask_dict in subtasks.items():
            subtask = cls.from_dict(subtask_dict, subtask_name, task)
            task.add_subtask(subtask)
        return task

    def write(self, file_path):
        """Write this task item to a json file, using the to_dict string.

        Args:
            file_path (str): path to the json file.
        """
        if not os.path.isdir(os.path.dirname(file_path)):
            raise TaskFileError(
                "Task file directory {0} does not exist".format(
                    file_path
                )
            )
        if os.path.splitext(file_path)[-1] != ".json":
            raise TaskFileError(
                "Task file path {0} is not a json.".format(file_path)
            )
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=4)

    @classmethod
    def from_file(cls, file_path, parent=None):
        """Initialise class from json file.

        Args:
            file_path (str): path to the json file.
            parent (Task or TaskCategory or None): parent of task.

        Returns:
            (Task): Task item described by json file.
        """
        if not os.path.isfile(file_path):
            raise TaskFileError(
                "Task file {0} does not exist".format(file_path)
            )
        with open(file_path, "r") as file_:
            file_text = file_.read()
        try:
            task_dict = json.loads(file_text, object_pairs_hook=OrderedDict)
        except json.JSONDecodeError:
            raise TaskFileError(
                "Tasks file {0} is incorrectly formatted for json load".format(
                    file_path
                )
            )
        name = os.path.splitext(os.path.basename(file_path))[0]
        return cls.from_dict(task_dict, name, parent)


class TaskHistory(object):
    """Simple wrapper around an OrderedDict to represent task history.
    
    The structure of a task history dict is like this:
    {
        date_1: {
            status: task_status,
            comments: {
                time_1: comment_1,
                time_2: comment_2,
                ...
            }
        },
        ...
    }
    """

    def __init__(self, task):
        """Initialise task history object.

        Args:
            task (Task): the task that this represents the history of.
        """
        self.task = task
        self.dict = OrderedDict()

    def __bool__(self):
        """Override bool operator to indicate whether dictionary is filled.

        Returns:
            (bool): False if dictionary is empty, else True.
        """
        return bool(self.dict)

    def update(self, date_time, status, comment=None):
        """Update task history and status.

        Args:
            date (datetime.datetime): datetime object to update task with.
            status (TaskStatus): status to update task with.
            comment (str): comment to add to history if needed.
        """
        date = date_time.date()
        date_entry = self.dict.setdefault(date, dict())
        date_entry["status"] = status
        if comment:
            comments = date_entry.setdefault("comments", OrderedDict())
            comments[date_time] = comment
