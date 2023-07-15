"""Task class."""

from collections import OrderedDict

from scheduler.api.common.date_time import Date
from scheduler.api.common.object_wrappers import (
    HostedDataDict,
    MutableAttribute,
)
from scheduler.api.serialization import item_registry
from scheduler.api.serialization.serializable import SaveType
from scheduler.api.enums import (
    ItemImportance,
    ItemStatus,
    ItemSize,
    OrderedStringEnum,
)
from .base_task_item import BaseTaskItem
from .task_history import TaskHistory, TaskType


class TaskValueType(OrderedStringEnum):
    """Enumeration for task value types."""
    NONE = ""
    TIME = "Time"
    STRING = "String"
    INT = "Int"
    FLOAT = "Float"
    MULTI = "Multi"


class Task(BaseTaskItem):
    """Class representing a generic task."""
    _SAVE_TYPE = SaveType.FILE

    TASKS_KEY = "subtasks"
    HISTORY_KEY = "history"
    STATUS_KEY = "status"
    TYPE_KEY = "type"
    VALUE_TYPE_KEY = "value_type"
    SIZE_KEY = "size"
    IMPORTANCE_KEY = "importance"
    ID_KEY = "id"

    DEFAULT_NAME = "task"

    def __init__(
            self,
            name,
            parent=None,
            task_type=None,
            status=None,
            history_dict=None,
            value_type=None,
            size=None,
            importance=None):
        """Initialise task class.

        Args:
            name (str): name of task.
            parent (Task or None): parent of current task, if task is subtask.
            task_type (TaskType or None): type of task (routine or general).
                if None, we default to general.
            status (ItemStatus or None): status of current task. If None,
                we default to unstarted.
            history_dict (OrderedDict or None): serialized task history dict,
                if exists.
            value_type (TaskValueType or None): task value type, if not None.
            size (ItemSize or None): task size, if given.
            importance (ItemImportance or None): task importance, if given.
        """
        super(Task, self).__init__(name, parent)
        self._type = MutableAttribute(
            task_type or TaskType.GENERAL,
            "type"
        )
        self._status = MutableAttribute(
            status or ItemStatus.UNSTARTED,
            "status",
        )
        self._history = (
            TaskHistory.from_dict(history_dict, self)
            if history_dict is not None
            else TaskHistory(self)
        )
        self.value_type = value_type or TaskValueType.NONE
        self._size = MutableAttribute(
            size or ItemSize.NONE,
            "size"
        )
        self._importance = MutableAttribute(
            importance or ItemImportance.NONE,
            "importance"
        )
        self._is_tracked = MutableAttribute(False, "is_tracked")
        self._allowed_child_types = [Task]

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
            (ItemStatus): current status.
        """
        return self.history.get_status_at_date(Date.now())
        # TODO: keep an eye that it's fine to use date not datetime
        # return self.history.get_status_at_datetime(DateTime.now())

        # I'm changing this to just find status at the current datetime, as it
        # needs to update as the time changes.
        # TODO: keep an eye on if this seems to slow stuff down considerably.
        # there's definitely stuff I can do with caching to speed it up
        # TODO: delete below and notes above when I'm more confident, and
        # delete the _status attribute, plus its corresponding logic in the
        # to_dict and from_dict methods
        if (self.type == TaskType.ROUTINE
                and self._status.value == ItemStatus.COMPLETE):
            last_completed = self.history.last_completed
            if last_completed and last_completed != Date.now():
                # date_completed = self.history.last_completed
                # current_date = Date.now()
                # if date_completed != current_date:
                    # TODO: should this update the task history too?
                    # probably not but really these statuses are not ideal
                    # for routines. Ultimately I do think routines need their
                    # own subclass, which may mean TaskTypes become unneeded.
                self._status.set_value(ItemStatus.UNSTARTED)
        return self._status.value

    @property
    def type(self):
        """Get task type.

        Returns:
            (TaskType): current status.
        """
        return self._type.value

    @property
    def size(self):
        """Get task size.

        Returns:
            (ItemSize): task size.
        """
        return self._size.value

    @property
    def importance(self):
        """Get task size.

        Returns:
            (ItemImportance): task importance.
        """
        return self._importance.value

    @property
    def is_tracked(self):
        """Find out if task is tracked or not.

        Returns:
            (Bool): whether or not task is tracked.
        """
        return self._is_tracked.value

    @property
    def history(self):
        """Get task history.

        Returns:
            (TaskHistory): task history.
        """
        return self._history

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

    def get_status_at_date(self, date):
        """Get task status at given date.

        Args:
            date (Date): date to query.

        Returns:
            (ItemStatus): task status at given date.
        """
        return self.history.get_status_at_date(date)

    def get_value_at_date(self, date):
        """Get task value at given date.

        Args:
            date (Date): date to query.

        Returns:
            (variant or None): task value at given date, if set.
        """
        return self.history.get_value_at_date(date)

    def clone(self):
        """Create skeletal clone of item, missing parent and children.

        Returns:
            (Task): cloned item.
        """
        task = Task(
            self.name,
            parent=None,
            task_type=self.type,
            status=self.status,
            history_dict=self.history.to_dict(),
            value_type=self.value_type,
        )
        task._color = self._color
        return task

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
            self.ID_KEY: self._get_id(),
        }
        if self.history:
            json_dict[self.HISTORY_KEY] = self.history.to_dict()
        if self.value_type:
            json_dict[self.VALUE_TYPE_KEY] = self.value_type
        if self.size:
            json_dict[self.SIZE_KEY] = self.size
        if self.importance:
            json_dict[self.IMPORTANCE_KEY] = self.importance
        if self._subtasks:
            subtasks_dict = OrderedDict()
            for subtask_name, subtask in self._subtasks.items():
                subtasks_dict[subtask_name] = subtask.to_dict()
            json_dict[self.TASKS_KEY] = subtasks_dict
        return json_dict

    @classmethod
    def from_dict(cls, json_dict, name, history_data=None, parent=None):
        """Initialise class from dictionary representation.

        The json_dict is expected to be structured as described in the to_dict
        docstring.

        Args:
            json_dict (OrderedDict): dictionary representation.
            name (str): name of task.
            history_data (HistoryData or None): history data struct to fill
                with task history.
            parent (Task, TaskCategory or None): parent of task.

        Returns:
            (Task): task class for given dict.
        """
        task_type = json_dict.get(cls.TYPE_KEY, None)
        task_status = json_dict.get(cls.STATUS_KEY, None)
        if task_status is not None:
            task_status = ItemStatus(task_status)
        task_history = json_dict.get(cls.HISTORY_KEY, None)
        value_type = json_dict.get(cls.VALUE_TYPE_KEY, None)
        size = json_dict.get(cls.SIZE_KEY, None)
        importance = json_dict.get(cls.IMPORTANCE_KEY, None)
        task = cls(
            name,
            parent,
            task_type,
            task_status,
            task_history,
            value_type,
            size,
            importance,
        )
        task._activate()
        id = json_dict.get(cls.ID_KEY, None)
        if id is not None:
            # TODO: this bit means tasks are now added to the item registry.
            # This was done to make deserialization of task history dicts
            # work. Keep an eye on this, I want to make sure it doesn't slow
            # down loading too much.
            item_registry.register_item(id, task)
        if history_data:
            for date, subdict in task._history.iter_date_dicts():
                history_data._add_data(date, task, subdict)

        subtasks = json_dict.get(cls.TASKS_KEY, {})
        for subtask_name, subtask_dict in subtasks.items():
            subtask = cls.from_dict(
                subtask_dict,
                subtask_name,
                history_data=history_data,
                parent=task,
            )
            task._children[subtask_name] = subtask
        return task
