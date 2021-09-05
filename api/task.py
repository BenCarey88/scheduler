"""Task class."""

from collections import OrderedDict


class SubtaskNameError(Exception):
    """Exception for when multiple subtasks have the same name."""
    def __init__(self, task_name, subtask_name):
        """Initialise exception.

        Args:
            task_name (str): name of task we're adding subtask to.
            subtask_name (str): name of subtask.
        """
        message = "subtask of {0} with name {1} already exists".format(
            task_name, subtask_name
        )
        super(Exception, self).__init__(message)


class SubtaskParentError(Exception):
    """Exception for when subtask does not have current task as a parent."""
    pass


class TaskType():
    """Enumeration for task types."""
    ROUTINE = "Routine"
    GENERAL = "General"


class TaskStatus():
    """Enumeration for task statuses."""
    UNSTARTED = "Unstarted"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"


class Task(object):
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
        self.name = name
        self.parent = parent
        self._subtasks = OrderedDict()
        self.type = task_type or TaskType.GENERAL
        self.status = status or TaskStatus.UNSTARTED
        self.history = history or TaskHistory(self)

    def create_subtask(
            self,
            name,
            task_type=None,
            status=None,
            history=None):
        """Create subtask and add to task subtasks dict.

        Raises:
            (SubtaskNameError): if a subtask with given name already exists.

        Args:
            name (str): name of subtask.
            task_type (TaskType or None): type of subtask (routine or general).
                if None, we default to current task type.
            status (TaskStatus or None): status of subtask. If None, we default
                to unstarted.
            history (TaskHistory or None): subtask history, if exists.

        Returns:
            (Task): newly created subtask.
        """
        if name in self._subtasks:
            raise SubtaskNameError(self.name, name)
        subtask = Task(
            name,
            parent=self,
            task_type=task_type or self.type,
            status=status,
            history=history
        )
        self._subtasks[name] = subtask
        return subtask

    def add_subtask(self, task):
        """Add an existing subtask to this task's subtasks dict.

        Args:
            task (Task): subtask Task object to add.

        Raises:
            (SubtaskNameError): if a subtask with given name already exists.
            (SubtaskParentError): if the subtask has a different task as a
                parent.
        """
        if task.name in self._subtasks:
            raise SubtaskNameError(self.name, task.name)
        if not task.parent:
            task.parent = self
        if task.parent != self:
            raise SubtaskParentError(
                "subtask {0} has incorrect patent: {1} instead of {2}".format(
                    task.name, task.parent.name, self.name
                )
            )
        self._subtasks[task.name] = task

    def get_subtask(self, name):
        """Get subtask by name.

        Args:
            name (str): name of subtask.

        Returns:
            (Task or None): subtask, if one by that name exits.
        """
        return self._subtasks.get(name, None)

    def get_subtask_at_index(self, index):
        """Get subtask by index.

        Args:
            index (int): index of subtask.

        Returns:
            (Task or None): subtask, if one of that index exits.
        """
        if 0 <= index < len(self._subtasks):
            return list(self._subtasks.values())[index]
        return None

    def get_all_subtasks(self):
        """Get all subtasks of task.

        Returns:
            (list(Task)): list of all subtasks of task.
        """
        return list(self._subtasks.values())

    def num_subtasks(self):
        """Get number of subtasks of this task.

        Returns:
            (int): number of subtasks.
        """
        return len(self._subtasks)

    def index(self):
        """Get index of this task as a subtask of its parent task.

        Returns:
            (int): index of task.
        """
        if not self.parent:
            return None
        else:
            return self.parent.get_all_subtasks().index(self)

    def is_leaf(self):
        """Return whether or not task is a leaf (ie has no subtasks).

        Returns:
            (bool): True if task is leaf, else False.
        """
        return not bool(self._subtasks)

    def is_subtask(self):
        """Return whether or not task is a subtask.

        Returns:
            (bool): True if task is subtask, else False.
        """
        return (self.parent is not None)

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
        to be added as a key to this dictionary in the tasks json files (see
        the tasks_data module for details on this).

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
        """Initialize class from dictionary representation.

        The json_dict is expected to be structured as described in the to_dict
        docstring.

        Args:
            json_dict (OrderedDict): dictionary representation.
            name (str): name of task.
            parent (Task or None): parent of current task, if task is subtask.

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
        """Override bool operator to depend on whether dictionary is filled.

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
