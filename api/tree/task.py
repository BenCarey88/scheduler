"""Task class."""

from collections import OrderedDict
from functools import partial
import json
import os

from scheduler.api.common.date_time import Date, DateTime
from scheduler.api.edit.task_edit import (
    ChangeTaskTypeEdit,
    UpdateTaskHistoryEdit
)
from scheduler.api.serialization.serializable import SaveType

from ._base_tree_item import BaseTreeItem


class TaskType():
    """Enumeration for task types."""
    ROUTINE = "Routine"
    GENERAL = "General"


class TaskStatus():
    """Enumeration for task statuses."""
    UNSTARTED = "Unstarted"
    IN_PROGRESS = "In Progress"
    COMPLETE = "Complete"


class TaskValueType():
    """Enumeration for task value types."""
    NONE = None
    TIME = "Time"
    STRING = "String"
    INT = "Int"
    FLOAT = "Float"
    MULTI = "Multi"


class Task(BaseTreeItem):
    """Class representing a generic task."""
    _SAVE_TYPE = SaveType.FILE

    TASKS_KEY = "subtasks"
    HISTORY_KEY = "history"
    STATUS_KEY = "status"
    TYPE_KEY = "type"
    VALUE_TYPE_KEY = "value_type"

    def __init__(
            self,
            name,
            parent=None,
            task_type=None,
            status=None,
            history=None,
            value_type=None):
        """Initialise task class.

        Args:
            name (str): name of task.
            parent (Task or None): parent of current task, if task is subtask.
            task_type (TaskType or None): type of task (routine or general).
                if None, we default to general.
            status (TaskStatus or None): status of current task. If None,
                we default to unstarted.
            history (TaskHistory or None): task history, if exists.
            value_type (TaskValueType or None): task value type, if not None.
        """
        super(Task, self).__init__(name, parent)
        self._type = task_type or TaskType.GENERAL
        self._status = status or TaskStatus.UNSTARTED
        self.history = history if history is not None else TaskHistory()
        self.value_type = value_type or TaskValueType.NONE
        self._allowed_child_types = [Task]

        # new attribute and method names for convenience
        # TODO: it's a faff to keep adding these redefinitions
        # remove all the ones that aren't necessary.
        self.create_subtask = partial(
            self.create_child,
            task_type=self.type
        )
        self.create_new_subtask = partial(
            self.create_new_child,
            default_name="subtask",
            task_type=self.type,
        )
        # TODO: task type stuff getting messy - if this attribute remains a
        # thing, we should ensure that any child added through add_child has
        # the same type.
        self.add_subtask = self.add_child
        self.create_sibling_task = partial(
            self.create_sibling,
            task_type=self.type,
        )
        self.create_new_sibling_task = partial(
            self.create_new_sibling,
            default_name = "task",
            task_type=self.type,
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

    # TODO: should routine be subclass? If so will need to think about what
    # that means for the rest of the code.
    # TODO: need to work out how the following code will work with undo/redo
    # for the most part I expect it will only effect things between sessions
    # but should have a plan for it.
    @property
    def status(self):
        """Get task status.

        Implementing this as a getter allows us to reset status in the case of
        routines, which are time based.

        Returns:
            (TaskStatus): current status.
        """
        if (self.type == TaskType.ROUTINE 
                and self._status == TaskStatus.COMPLETE):
            last_completed = self.history.last_completed
            if last_completed:
                date_completed = self.history.last_completed
                current_date = Date.now()
                if date_completed != current_date:
                    # TODO: should this update the task history too?
                    # probably not but really these statuses are not ideal
                    # for routines. Ultimately I do think routines need their
                    # own subclass, which may mean TaskTypes become unneeded.
                    self._status = TaskStatus.UNSTARTED
        return self._status

    # TODO: do we need this? Currently status seter is used by edit class,
    # but that's a friend so is free to use _status, and other classes
    # shouldn't be setting this directly anyway.
    # does allow to set recursively though which we probably want down
    # the line.
    @status.setter
    def status(self, value):
        """Set task status.

        Args:
            (TaskStatus): new status value.
        """
        self._status = value

    @property
    def type(self):
        """Get task type.

        Returns:
            (TaskType): current status.
        """
        return self._type

    @type.setter
    def type(self, value):
        """Set task type.

        Also update type for all parents and children.

        Args:
            (TaskType): new type value.
        """
        self._type = value
        parent = self.parent
        while isinstance(parent, Task) and parent.type != value:
            parent._type = value
            parent = parent.parent
        for subtask in self._children.values():
            if subtask.type != value:
                subtask.type = value

    # TODO: I made what I now feel was a pretty big ballsup with my
    # classifications, and at the moment everything I've made a top-level
    # task should I think be a bottom-level category, so I should make a
    # new function here to reflect that once I've refactored.
    def top_level_task(self):
        """Get top level task that this task is a subtask of.

        Returns:
            (Task): top level task item.
        """
        top_level_task = self
        while isinstance(top_level_task.parent, Task):
            top_level_task = top_level_task.parent
        return top_level_task

    def is_subtask(self):
        """Check whether this task is a subtask of some other task.

        Returns:
            (bool): whether or not task is a subtask.
        """
        return isinstance(self.parent, Task)

    def update_task(self, status=None, date_time=None, comment=None):
        """Update task history and status.

        Args:
            status (TaskStatus or None): status to update task with. If None
                given, we calculate the next one.
            date (DateTime or None): datetime object to update task history
                with.
            comment (str): comment to add to history if needed.
        """
        if status is None:
            current_status = self.status
            if current_status == TaskStatus.UNSTARTED:
                if self.type == TaskType.ROUTINE:
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
            self,
            date_time,
            status,
            comment=comment,
            register_edit=self._register_edits,
        )

    def change_task_type(self, new_type):
        """Change task type to new type.

        Args:
            new_type (TaskType): new type to change to.
        """
        if new_type != self.type:
            ChangeTaskTypeEdit.create_and_run(
                self,
                new_type,
                self._register_edits
            )

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
            self.STATUS_KEY: self.status,
            self.TYPE_KEY: self.type,
        }
        if self.history:
            json_dict[self.HISTORY_KEY] = self.history.dict
        if self.value_type:
            json_dict[self.VALUE_TYPE_KEY] = self.value_type
        if self._subtasks:
            subtasks_dict = OrderedDict()
            for subtask_name, subtask in self._subtasks.items():
                subtasks_dict[subtask_name] = subtask.to_dict()
            json_dict[self.TASKS_KEY] = subtasks_dict
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
        task_type = json_dict.get(cls.TYPE_KEY, None)
        task_status = json_dict.get(cls.STATUS_KEY, None)
        task_history = json_dict.get(cls.HISTORY_KEY, None)
        value_type = json_dict.get(cls.VALUE_TYPE_KEY, None)
        task = cls(
            name,
            parent,
            task_type,
            task_status,
            TaskHistory(task_history),
            value_type
        )

        subtasks = json_dict.get(cls.TASKS_KEY, {})
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
            value: task_value,
            comments: {
                time_1: comment_1,
                time_2: comment_2,
                ...
            }
        },
        ...
    }
    """
    STATUS_KEY = "status"
    VALUE_KEY = "value"
    COMMENTS_KEY = "comments"

    def __init__(self, history_dict=None):
        """Initialise task history object.

        Args:
            history_dict (OrderedDict or None): the ordered dict representing
                the history.
        """
        self.dict = history_dict or OrderedDict()

    def __bool__(self):
        """Override bool operator to indicate whether dictionary is filled.

        Returns:
            (bool): False if dictionary is empty, else True.
        """
        return bool(self.dict)

    def __nonzero__(self):
        """Override bool operator (python 2.x).

        Returns:
            (bool): False if dictionary is empty, else True.
        """
        return bool(self.dict)

    @property
    def last_completed(self):
        """Get date that this task was last completed.

        This is used in the case of routines.

        Returns:
            (Date or None): date of last completion, if exists.
        """
        for date, subdict in reversed(self.dict.items()):
            if subdict.get(self.STATUS_KEY) == TaskStatus.COMPLETE:
                return Date.from_string(date)
        return None
