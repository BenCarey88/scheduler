"""Task class."""

from collections import OrderedDict
from copy import copy
from functools import partial

from scheduler.api.common.date_time import Date, DateTime, Time, TimeDelta
from scheduler.api.common.object_wrappers import (
    HostedDataDict,
    MutableAttribute,
)
from scheduler.api.common.timeline import TimelineDict
from scheduler.api.serialization import item_registry
from scheduler.api.serialization.serializable import SaveType
from scheduler.api.enums import OrderedStringEnum, ItemStatus
from scheduler.api.utils import fallback_value, print_dict, setdefault_not_none

from .base_task_item import BaseTaskItem


class TaskType(OrderedStringEnum):
    """Enumeration for task types."""
    ROUTINE = "Routine"
    GENERAL = "General"


# class TaskStatus(OrderedStringEnum):
#     """Enumeration for task statuses."""
#     UNSTARTED = "Unstarted"
#     IN_PROGRESS = "In Progress"
#     COMPLETE = "Complete"


class TaskValueType(OrderedStringEnum):
    """Enumeration for task value types."""
    NONE = ""
    TIME = "Time"
    STRING = "String"
    INT = "Int"
    FLOAT = "Float"
    MULTI = "Multi"


# class TaskSize(OrderedStringEnum):
#     """Struct to store size types of task."""
#     NONE = ""
#     SMALL = "small"
#     MEDIUM = "medium"
#     BIG = "big"


# class TaskImportance(OrderedStringEnum):
#     """Struct to store levels of importance for task."""
#     NONE = ""
#     MINOR = "minor"
#     MODERATE = "moderate"
#     MAJOR = "major"
#     CRITICAL = "critical"


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
        self._size = MutableAttribute(size, "size")
        self._importance = MutableAttribute(importance, "importance")
        self._history_influencers = HostedDataDict(host_keys=True)
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


# TODO: fix serialization, and maybe add some value caching for date vals?
class TaskHistory(object):
    """Simple wrapper around an OrderedDict to represent task history.

    The structure of a task history dict is like this:
    {
        date_1: {
            status: task_status,
            value: task_value,
            status_override: True,
            comment: comment,
            influencers: {...},
            times: {
                time_1: {
                    status: status_1,
                    value: value_1,
                    comment: comment_1,
                    status_override: True,
                    influencers: {
                        influencer_1: {
                            status: status_1.1,
                            value: value_1.1,
                            comment: comment_1.1,
                            status_override: True,
                        }
                        influencer_2: {
                            status: status1.2,
                            value: value_1.2,
                        },
                        ...
                    },
                },
                time_2: {
                    status: status_2,
                    value: value_2,
                    comment: comment_2,
                    influencers: {...},
                },
                ...
            },
        },
        ...
    }
    """
    STATUS_KEY = "status"
    VALUE_KEY = "value"
    COMMENT_KEY = "comment"
    INFLUENCERS_KEY = "influencers"
    TIMES_KEY = "times"
    STATUS_OVERRIDE_KEY = "status_override"
    CORE_FIELD_KEYS = [STATUS_KEY, VALUE_KEY, STATUS_OVERRIDE_KEY]

    def __init__(self, task):
        """Initialise task history object.

        Args:
            task (Task): task this is describing the history of.
        """
        self._task = task
        self._dict = TimelineDict()

    def __bool__(self):
        """Override bool operator to indicate whether dictionary is filled.

        Returns:
            (bool): False if dictionary is empty, else True.
        """
        return bool(self._dict)

    def __nonzero__(self):
        """Override bool operator (python 2.x).

        Returns:
            (bool): False if dictionary is empty, else True.
        """
        return bool(self._dict)

    @property
    def last_completed(self):
        """Get date that this task was last completed.

        This is used in the case of routines.

        Returns:
            (Date or None): date of last completion, if exists.
        """
        for date in reversed(self._dict):
            subdict = self._dict[date]
            if subdict.get(self.STATUS_KEY) == ItemStatus.COMPLETE:
                return date
        return None

    # TODO: replace with utils.print_dict? May need to add in a key ordering
    # arg to that.
    def print(self):
        """Print history dict to terminal."""
        print_dict(
            self._dict,
            key_ordering=self.CORE_FIELD_KEYS+[
                self.COMMENT_KEY,
                self.INFLUENCERS_KEY,
                self.TIMES_KEY,
            ],
            start_message="{0} History:\n-----------".format(
                self._task.name,
            ),
        )

    def get_dict_at_date(self, date):
        """Get dict describing task history at given date.

        Args:
            date (Date): date to query.

        Returns:
            (dict): subdict of internal dict for given date.
        """
        return self._dict.get(date, {})

    def get_dict_at_datetime(self, date_time):
        """Get dict describing task history at given datetime.

        Args:
            date_time (DateTime): datetime to query.

        Returns:
            (dict): subdict of internal dict for given date.
        """
        date_dict = self._dict.get(date_time.date(), {})
        times_dict = date_dict.get(self.TIMES_KEY, {})
        return times_dict.get(date_time.time(), {})

    def iter_date_dicts(self):
        """iterate through task history dicts for each recorded date.
        
        Yields:
            (Date): date of history.
            (dict): subdict of internal dict for that date.
        """
        for date, subdict in self._dict.items():
            yield date, subdict

    def find_influencer_at_date(self, date, influencer):
        """Search times dict at given date to find influencer.

        Args:
            date (Date): date to search at.
            influencer (HostedData): influencer to search for.

        Returns:
            (Time or None): first time that influencer appears, if found.
        """
        times_dict = self.get_dict_at_date(date).get(self.TIMES_KEY, {})
        for time, time_subdict in times_dict.items():
            if influencer in time_subdict.get(self.INFLUENCERS_KEY, {}):
                return time

    def get_status_at_date(self, date, start=False):
        """Get task status at given date.

        This searches through for the most complete status set since a status
        override before (or optionally including) this date, stopping at the
        start of the date if its a routine, and defaulting to unstarted.

        Note that this DOESN'T attempt to look at the time subdictionary or
        influencers subdicts. It is the responsibility of any edit that alters
        the status influencers to also propagate any status changes up to the
        current date.

        Args:
            date (Date): date to query.
            start (bool): if True, get status at start of date, otherwise get
                status at end of date.

        Returns:
            (ItemStatus): task status at start of given date.
        """
        status = None
        status_override = False
        if not start:
            date_dict = self.get_dict_at_date(date)
            status = date_dict.get(self.STATUS_KEY)
        if status is not None:
            status_override = date_dict.get(self.STATUS_OVERRIDE_KEY, False)
        status = status or ItemStatus.UNSTARTED
        # if status is overridden, or item is routine, don't check prev days
        if (status_override
                or status == ItemStatus.COMPLETE
                or self._task.type == TaskType.ROUTINE):
            return status

        # otherwise find the most complete status since an override
        for recorded_date in reversed(self._dict):
            if recorded_date < date:
                subdict = self._dict[recorded_date]
                new_status = subdict.get(self.STATUS_KEY, status)
                if new_status > status:
                    status = new_status
                status_override = subdict.get(
                    self.STATUS_OVERRIDE_KEY,
                    status_override,
                )
                if status_override or status == ItemStatus.COMPLETE:
                    break
        return status

    def get_value_at_date(self, date):
        """Get task value at given date.

        This just searches for any value set at the current date. Currently,
        since values are linked to routines and task tracking they're
        always assumed to reset at each date.

        Args:
            date (Date): date to query.

        Returns:
            (variant or None): task value at given date, if set.
        """
        return self.get_dict_at_date(date).get(self.VALUE_KEY, None)

    def get_status_at_datetime(self, date_time):
        """Get task status at given datetime.

        This searches through for the most complete status set since a status
        override up to this date, stopping at the start of the date if it's
        a routine, and defaulting to unstarted.

        Note that this DOESN'T attempt to look at the influencers subdicts.
        It is the responsibility of any edit that alters the status influencers
        to also propagate any status changes up to the time.

        Args:
            date_time (DateTime): datetime to query.

        Returns:
            (ItemStatus): task status at given datetime.
        """
        date_dict = self.get_dict_at_date(date_time.date())
        times_dict = date_dict.get(self.TIMES_KEY, {})
        status = ItemStatus.UNSTARTED
        status_override = False
        for time in reversed(times_dict):
            if time <= date_time.time():
                subdict = times_dict[time]
                new_status = subdict.get(self.STATUS_KEY, status)
                if new_status > status:
                    status = new_status
                status_override = subdict.get(
                    self.STATUS_OVERRIDE_KEY,
                    status_override,
                )
                if status_override or status == ItemStatus.COMPLETE:
                    return status
        if self._task.type == TaskType.ROUTINE:
            return status
        prev_status = self.get_status_at_date(date_time.date(), start=True)
        if prev_status > status:
            return prev_status
        return status

    def get_value_at_datetime(self, date_time):
        """Get task value at given datetime.

        Currently this works by the following logic: if there are values
        set at or before this time in the date, pick the most recent one.
        Otherwise, find the value set at the date of the previous day.
        Values on the current day are considered to be completed at the
        very end of the day, so won't apply to a datetime within the day.

        Args:
            date_time (DateTime): datetime to query.

        Returns:
            (variant or None): task value at given datetime, if set.
        """
        date_dict = self.get_dict_at_date(date_time.date())
        times_dict = date_dict.get(self.TIMES_KEY, {})
        for time in reversed(times_dict):
            subdict = times_dict.get(time)
            if self.VALUE_KEY in subdict and time <= date_time.time():
                return subdict[self.VALUE_KEY]
        return self.get_value_at_date(date_time.date() - TimeDelta(days=1))

    def get_influencers_dict(self, date_time):
        """Get influencers dict for given date or datetime.

        Args:
            date_time (Date or DateTime): date or datetime to check.

        Returns:
            (HostedDataDict): influencers dict.
        """
        datetime_dict = {}
        if isinstance(date_time, DateTime):
            datetime_dict = self.get_dict_at_datetime(date_time)
        elif isinstance(date_time, Date):
            datetime_dict = self.get_dict_at_date(date_time)
        return datetime_dict.get(self.INFLUENCERS_KEY, {})

    def get_influencer_dict(self, date_time, influencer):
        """Get influencer dict for given date or datetime and influencer.

        Args:
            date_time (Date or DateTime): date or datetime to check.
            influencer (HostedData): influencer to check for

        Returns:
            (dict): influencer dict.
        """
        return self.get_influencers_dict(date_time).get(influencer, {})

    def get_influenced_status(self, date_time, influencer):
        """Get status defined by given influencer at given datetime, if exists.

        Args:
            date_time (Date or DateTime): date or datetime to check.
            influencer (variant): item to check.

        Returns:
            (ItemStatus or None): status, if found.
        """
        return self.get_influencer_dict(date_time, influencer).get(
            self.STATUS_KEY
        )

    def get_influenced_value(self, date_time, influencer):
        """Get value defined by given influencer at given datetime, if exists.

        Args:
            date_time (Date or DateTime): date or datetime to check.
            influencer (variant): item to check.

        Returns:
            (variant or None): value, if found.
        """
        return self.get_influencer_dict(date_time, influencer).get(
            self.VALUE_KEY
        )

    def _get_update_edit_diff_dict(
            self,
            influencer,
            old_datetime=None,
            new_datetime=None,
            core_field_updates=None):
        """Get diff dicts for UpdateTaskHistoryEdit.

        Args:
            influencer (Hosted): the object that is influencing the update.
            old_datetime (Date, DateTime or None): the date or datetime that
                this influencer was previously influencing at. If not given,
                the edit will add it as a new influencer instead.
            new_datetime (Date, DateTime or None): the date or datetime that
                this update will be occurring at. If not given, the edit will
                just remove the influencer at the old time instead.
            core_field_updates (dict or None): dictionary of status, value and
                status overrides that the influencer will now be defining at
                the new date or time. Fields will be copied over from the old
                datetime if the influencer exists at that date/time, and then
                modified according to this dict - any field set to None will be
                deleted and any field with a defined value will be added or
                modified accordingly.

        Returns:
            (TimelineDict or None): diff dict, to be used to add, remove or
                modify history to update with the new data. This will be used
                with the ADD_REMOVE_OR_MODIFY dictionary edit operation.
        """
        if not core_field_updates and old_datetime is None:
            return None
        diff_dict = TimelineDict()

        # diff dict to remove influencer at old date time, and update
        self.__populate_diff_dict(
            diff_dict,
            influencer,
            old_datetime,
            new_datetime,
            core_field_updates,
            use_old=True,
        )
        # diff dict to add influencer at new date time, and update
        self.__populate_diff_dict(
            diff_dict,
            influencer,
            old_datetime,
            new_datetime,
            core_field_updates,
            use_old=False,
        )
        return diff_dict

    def __populate_diff_dict(
            self,
            diff_dict,
            influencer,
            old_datetime=None,
            new_datetime=None,
            core_field_updates=None,
            use_old=True):
        """Populate diff dict to remove or add influencer data.

        Args:
            diff_dict (dict): the overall diff dict we're building up.
            influencer (variant): the object that is influencing the update.
            old_datetime (Date, DateTime or None): the date or datetime that
                this influencer was previously influencing at. If not given,
                the edit will add it as a new influencer instead.
            new_datetime (Date, DateTime or None): the date or datetime that
                this update will be occurring at. If not given, the edit will
                just remove the influencer at the old time instead.
            core_field_updates (dict or None): dictionary of status, value and
                status overrides that the influencer will now be defining at
                the new date or time.
            use_old (bool): if True, we're populating the diff dict at the old
                date_time (ie. removing the old influencer data), else we're
                populating at the new date_time (ie. adding influencer data).
        """
        old_date = self.__get_date(old_datetime)
        new_date = self.__get_date(new_datetime)
        if use_old:
            date_time = old_datetime
            date = old_date
            influencer_dict_method = self.__get_old_influencers_diff_dict
        else:
            date_time = new_datetime
            date = new_date
            influencer_dict_method = self.__get_new_influencers_diff_dict

        # get influencer diff dict
        influencer_diff_dict = influencer_dict_method(
            influencer,
            old_datetime,
            new_datetime,
            core_field_updates,
        )
        if influencer_diff_dict is None:
            return

        # add influencer dict and propagate edits up to times level if needed
        date_diff_dict = self.__add_influencer_diff_dict_at_date_time(
            date_time,
            influencer_diff_dict,
            diff_dict,
            influencer,
        )

        # propagate edits up to dates level
        if use_old and old_date == new_date:
            # wait til the new date diff dict has been done to update
            return
        if date_diff_dict is None:
            # if date_diff_dict is None, whole date is removed, so we're done.
            return
        date_dict = self.get_dict_at_date(date)
        core_fields_dict = self.__find_core_fields_dict(
            date_dict.get(self.INFLUENCERS_KEY, {}),
            diff_dict=date_diff_dict.get(self.INFLUENCERS_KEY),
            fallback_dict=date_dict.get(self.TIMES_KEY, {}),
            fallback_diff_dict=date_diff_dict.get(self.TIMES_KEY),
        )
        for key in self.CORE_FIELD_KEYS:
            if core_fields_dict.get(key) != date_dict.get(key):
                date_diff_dict[key] = core_fields_dict[key]

    def __get_date(self, date_time):
        """Convenience method to get variables from a date or datetime.

        Args:
            date_time (Date, DateTime or None): datetime object to check.

        Returns:
            (Date or None): the date corresponding to the date_time object.
        """
        if isinstance(date_time, DateTime):
            return date_time.date()
        elif isinstance(date_time, Date):
            return date_time
        return None

    def __get_old_influencers_diff_dict(
            self,
            influencer,
            old_datetime=None,
            new_datetime=None,
            core_field_updates=None):
        """Get UpdateTaskHistoryEdit diff dict for influencers at old datetime.

        Args:
            influencer (variant): the object that is influencing the update.
            old_datetime (Date, DateTime or None): the date or datetime that
                this influencer was previously influencing at, if given.
            new_datetime (Date, DateTime or None): the date or datetime that
                the update will be occurring at, if given.
            core_field_updates (dict or None): dictionary of status, value and
                status overrides that the influencer will now be defining at
                the new date or time. This is included here for convenience,
                but not actually used.

        Returns:
            (dict or None): diff dict to be used to remove influencer data
                from the old datetime, if needed.
        """
        if old_datetime is None:
            # if no old_datetime given then no need to remove
            return None
        if old_datetime == new_datetime:
            # if datetimes are same, just use new influencer diff dict
            return None
        influencers_dict = self.get_influencers_dict(old_datetime)
        if influencer not in influencers_dict:
            return None
        if len(influencers_dict) == 1:
            # if this is the only influencer remove entire influencers dict
            return {self.INFLUENCERS_KEY: None}
        # otherwise remove this influencer dict
        return {self.INFLUENCERS_KEY: HostedDataDict({influencer: None})}

    def __get_new_influencers_diff_dict(
            self,
            influencer,
            old_datetime=None,
            new_datetime=None,
            core_field_updates=None):
        """Get UpdateTaskHistoryEdit diff dict for influencers at new datetime.

        Args:
            influencer (variant): the object that is influencing the update.
            old_datetime (Date, DateTime or None): the date or datetime that
                this influencer was previously influencing at, if given.
            new_datetime (Date, DateTime or None): the date or datetime that
                this update will be occurring at. If not given, the edit will
                just remove the influencer at the old time instead.
            core_field_updates (dict or None): dictionary of status, value and
                status overrides that the influencer will now be defining at
                the new date or time.

        Returns:
            (dict or None): diff dict to be used to add influencer data to the
                new datetime, if needed.
        """
        if new_datetime is None:
            return None
        # values will be ported over from the dict at the old datetime
        old_influencer_dict = self.get_influencer_dict(
            old_datetime,
            influencer,
        )
        # and they'll overwrite anything in the dict at the new datetime
        influencer_dict_to_overwrite = self.get_influencer_dict(
            new_datetime,
            influencer,
        )
        diff_dict = copy(core_field_updates)
        remove_all = True
        for key in self.CORE_FIELD_KEYS:
            if key in diff_dict:
                if remove_all and diff_dict[key] is not None:
                    remove_all = False
                if influencer_dict_to_overwrite.get(key) == diff_dict[key]:
                    del diff_dict[key]
            elif key in old_influencer_dict:
                remove_all = False
                diff_dict[key] = old_influencer_dict[key]
            elif key in influencer_dict_to_overwrite:
                diff_dict[key] = None
        if not diff_dict:
            return None
        if remove_all:
            # if we've removed all the properties, then remove the dict
            influencers_dict = self.get_influencers_dict(new_datetime)
            if len(influencers_dict) == 1:
                # if this is the only influencer remove entire influencers dict
                return {self.INFLUENCERS_KEY: None}
            # otherwise just remove this specific influencer dict
            return {self.INFLUENCERS_KEY: HostedDataDict({influencer: None})}
        # otherwise, return diff dict as usual
        return {self.INFLUENCERS_KEY: HostedDataDict({influencer: diff_dict})}

    # TODO: to make things clearer, we should call these args date_time_obj,
    # or just use separate date and time args.
    def __add_influencer_diff_dict_at_date_time(
            self,
            date_time,
            influencer_diff_dict,
            diff_dict,
            influencer):
        """Add influencer diff subdict to larger diff dict at date_time.

        Args:
            date_time (Date or DateTime): the date_time object we're adding at.
            influencer_diff_dict (dict): the diff dict for the influencer.
            diff_dict (dict): the larger diff dict that we're adding to.
            influencer (HostedData): the influencer being updated.

        Returns:
            (dict or None): for convenience this returns the diff dict at the
                date. If None, this means the diff dict is telling us to
                remove that date.
        """
        if isinstance(date_time, DateTime):
            # add influencer diff to time influencers
            date = date_time.date()
            time = date_time.time()
            date_diff_dict = setdefault_not_none(diff_dict, date, {})
            times_diff_dict = setdefault_not_none(
                date_diff_dict,
                self.TIMES_KEY,
                TimelineDict(),
            )
            time_diff_dict = setdefault_not_none(times_diff_dict, time, {})
            time_diff_dict[self.INFLUENCERS_KEY] = influencer_diff_dict[
                self.INFLUENCERS_KEY
            ]
            if influencer_diff_dict[self.INFLUENCERS_KEY] is None:
                # if removing all influencers at given time, propagate removal
                times_dict = self.get_dict_at_date(date).get(
                    self.TIMES_KEY, {}
                )
                if len(times_dict) == 1:
                    date_dict = self.get_dict_at_date(date)
                    if not date_dict.get(self.INFLUENCERS_KEY):
                        # case 1: removed all times and no influencers exist
                        # at date level, so we delete the whole date dict
                        diff_dict[date] = None
                    else:
                        # case 2: just removed all times, so delete times dict
                        date_diff_dict[self.TIMES_KEY] = None
                else:
                    # case 3: just removed a specific time, so delete that dict
                    date_diff_dict[self.TIMES_KEY][time] = None

            else:
                # otherwise propagate edits up to times level
                time_dict = self.get_dict_at_datetime(date_time)
                # Note we changed diff dict arg below in case where it's None
                # so that we know to remove the whole influencer dict
                core_fields_dict = self.__find_core_fields_dict(
                    time_dict.get(self.INFLUENCERS_KEY, {}),
                    diff_dict=fallback_value(
                        influencer_diff_dict.get(self.INFLUENCERS_KEY),
                        HostedDataDict({influencer: None}),
                    ),
                )
                for key in self.CORE_FIELD_KEYS:
                    if core_fields_dict.get(key) != time_dict.get(key):
                        time_diff_dict[key] = core_fields_dict[key]
        else:
            date = date_time
            date_diff_dict = setdefault_not_none(diff_dict, date, {})
            date_diff_dict[self.INFLUENCERS_KEY] = influencer_diff_dict[
                self.INFLUENCERS_KEY
            ]
            if (influencer_diff_dict[self.INFLUENCERS_KEY] is None and
                    not self.get_dict_at_date(date).get(self.TIMES_KEY)):
                # removing all influencers at date dict without times 
                diff_dict[date] = None
        return diff_dict[date]

    def __find_core_fields_dict(
            self,
            dict_,
            starting_values=None,
            diff_dict=None,
            fallback_dict=None,
            fallback_diff_dict=None):
        """Search through a dict to find the status and override it defines.

        This searches for the most recent value and the most complete status
        after a status override, if one exists (or the most complete status
        in the dict otherwise).

        The dict being searched through will be either an influencers dict or
        a times dict, so the keys are either influencers or times, and the
        values are subdicts defining core fields (status, value, override).
        This is true of all the args, except for starting_values, which is
        just a core_fields dictionary.

        Args:
            dict_ (dict): ordered dict to search through.
            starting_values (dict or None): if given, use this dict to define
                the initial values of the fields - used for recursive use of
                this method only.
            diff_dict (dict(variant, dict/None) or None): diff_dict defining
                updates to core values in subdicts, to include in search.
            fallback_dict (dict or None): dict to search through if some
                fields aren't found from first one.
            fallback_diff_dict (tuple(variant, dict/None) or None): diff dict
                to be used with fallback dict.

        Returns:
            (dict): dictionary defining status, value and status_override.
        """
        starting_values = starting_values or {}
        status = starting_values.get(self.STATUS_KEY, None)
        value = starting_values.get(self.VALUE_KEY, None)
        status_override = starting_values.get(self.STATUS_OVERRIDE_KEY, None)
        if diff_dict is not None:
            dict_ = copy(dict_)
            for new_key, diff_subdict in diff_dict.items():
                if diff_subdict is None:
                    # when new subdict is None, delete from dict
                    if new_key in dict_:
                        del dict_[new_key]
                else:
                    # otherwise just add/modify keys in subdict
                    orig_subdict = dict_.get(new_key, {})
                    copied_subdict = copy(orig_subdict)
                    for key in self.CORE_FIELD_KEYS:
                        if key in diff_subdict:
                            new_value = diff_subdict[key]
                            if new_value is None:
                                del copied_subdict[key]
                            else:
                                copied_subdict[key] = new_value
                    dict_[new_key] = copied_subdict

        for key in reversed(dict_):
            subdict = dict_[key]
            new_status = subdict.get(self.STATUS_KEY)
            new_value = subdict.get(self.VALUE_KEY)
            new_override = subdict.get(self.STATUS_OVERRIDE_KEY)
            if (status is None or
                    (not status_override and 
                     new_status is not None and
                     new_status > status)):
                status = new_status
            if value is None and new_value is not None:
                value = new_value
            if new_override and not status_override:
                status_override = new_override
            # break once we've found value and status
            if (value is not None and
                    (status_override or status == ItemStatus.COMPLETE)):
                break

        core_fields_dict = {
            self.STATUS_KEY: status,
            self.VALUE_KEY: value,
            self.STATUS_OVERRIDE_KEY: status_override,
        }
        if (fallback_dict is not None and
                (status is None or value is None or not status_override)):
            return self.__find_core_fields_dict(
                fallback_dict,
                starting_values=core_fields_dict,
                diff_dict=fallback_diff_dict,
            )
        return core_fields_dict
    
    def _subdict_to_json_dict(self, subdict, include_influencers_key=False):
        """Utility to turn a date, time or influencer subdict to json dict.

        Args:
            subdict (dict): subdict to turn.
            include_influencers_key (bool): if True, also search for
                influencers key in subdict.

        Returns:
            (dict): json-formatted subdict.
        """
        json_subdict = {}
        # TODO: if we have any value that need converting, use
        # this to do so - atm time values are saved as strings, but
        # should probably save them as Times and create a converter
        # function to sort this
        keys_and_converters = [
            (self.STATUS_KEY, None),
            (self.STATUS_OVERRIDE_KEY, None),
            (self.VALUE_KEY, None),
            (self.COMMENT_KEY, None),
        ]
        for key, converter in keys_and_converters:
            if key in subdict:
                if converter is None:
                    json_subdict[key] = subdict[key]
                else:
                    json_subdict[key] = converter(subdict[key])

        if include_influencers_key and self.INFLUENCERS_KEY in subdict:
            json_inf_subdict = OrderedDict()
            for inf, inf_subdict in subdict[self.INFLUENCERS_KEY].items():
                # TODO: this currently assumes only tasks, planned items and
                # scheduled items can be influencers. May need updating?
                inf_key = inf._get_id()
                json_inf_subdict[inf_key] = self._subdict_to_json_dict(
                    inf_subdict
                )
            json_subdict[self.INFLUENCERS_KEY] = json_inf_subdict
        return json_subdict

    @classmethod
    def _subdict_from_json_dict(
            cls,
            json_dict,
            include_influencers_key=False,
            task_history_item=None,
            date_time_obj=None):
        """Utility to get a date, time or influencer subdict from a json dict.

        Args:
            json_dict (dict): json subdict to turn.
            include_influencers_key (bool): if True, also search for
                influencers key in subdict.
            task_history_item (TaskHistory): the history item being
                created.
            date_time_obj (Date or DateTime)

        Returns:
            (dict): subdict for use in class instance.
        """
        subdict = {}
        keys_and_converters = [
            (cls.STATUS_KEY, ItemStatus),
            (cls.STATUS_OVERRIDE_KEY, None),
            (cls.VALUE_KEY, None),
            (cls.COMMENT_KEY, None),
        ]
        for key, converter in keys_and_converters:
            if key in json_dict:
                if converter is None:
                    subdict[key] = json_dict[key]
                else:
                    subdict[key] = converter(json_dict[key])

        if include_influencers_key and cls.INFLUENCERS_KEY in json_dict:
            if date_time_obj is None or task_history_item is None:
                raise Exception(
                    "Need date_time_obj and task_history_item args"
                )
            for id, json_inf_subdict in json_dict[cls.INFLUENCERS_KEY].items():
                # TODO this currently assumes only tasks, planned items
                # and scheduled items can be influencers. May need updating?
                # ALSO TODO: will this crash if the task influences itself
                # because it tries to add an inactive hosted data item to
                # a hosted data dict? I think it's safe based on the order
                # of things done in the task from_dict method, but should
                # keep an eye out
                item_registry.register_callback(
                    id,
                    partial(
                        task_history_item.__add_influencer,
                        date_time_obj,
                        cls._subdict_from_json_dict(json_inf_subdict),
                    ),
                )
        return subdict

    def __add_influencer(self, date_time_obj, influence_dict, influencer):
        """Add influencer (to be used during deserialization).

        Args:
            influencer (HostedData): the influencing item to add.
            date_time_obj (Date or DateTime): datetime to add at.
            influence_dict (dict): dictionary of status and values set by
                this influencer.
        """
        date = date_time_obj
        time = None
        if isinstance(date_time_obj, DateTime):
            date = date_time_obj.date()
            time = date_time_obj.time()
        date_or_time_dict = self._dict.setdefault(date, {})
        if time is not None:
            times_dict = date_or_time_dict.setdefault(
                self.TIMES_KEY,
                TimelineDict(),
            )
            date_or_time_dict = times_dict.setdefault(time, {})
        influencers_dict = date_or_time_dict.setdefault(
            self.INFLUENCERS_KEY,
            HostedDataDict(),
        )
        influencers_dict[influencer] = influence_dict

    # TODO: make these work with status overrides, influencers etc.
    def to_dict(self):
        """Convert class to serialized json dict.

        In practice, this just converts the Date and Time objects to strings.

        Returns:
            (OrderedDict): json dict.
        """
        json_dict = OrderedDict()
        for date, subdict in self._dict.items():
            json_subdict = self._subdict_to_json_dict(subdict, True)
            if self.TIMES_KEY in subdict:
                json_times_subdict = OrderedDict()
                json_subdict[self.TIMES_KEY] = json_times_subdict
                for time, time_subdict in subdict[self.TIMES_KEY].items():
                    json_time_subdict = self._subdict_to_json_dict(
                        time_subdict,
                        include_influencers_key=True,
                    )
                    json_times_subdict[time.string()] = json_time_subdict
            if json_subdict:
                json_dict[date.string()] = json_subdict
        return json_dict

    @classmethod
    def from_dict(cls, json_dict, task):
        """Initialise class from dictionary representation.

        Args:
            json_dict (OrderedDict): dictionary representation.
            task (Task): task this is describing the history of.

        Returns:
            (TaskHistory): task history class with given dict.
        """
        task_history = cls(task)
        class_dict = TimelineDict()
        task_history._dict = class_dict
        for date_str, subdict in json_dict.items():
            date = Date.from_string(date_str)
            class_subdict = cls._subdict_from_json_dict(
                subdict,
                include_influencers_key=True,
                task_history_item=task_history,
                date_time_obj=date,
            )
            class_dict[date] = class_subdict
            if cls.TIMES_KEY in subdict:
                class_times_subdict = TimelineDict()
                class_subdict[cls.TIMES_KEY] = class_times_subdict
                for time_str, time_subdict in subdict[cls.TIMES_KEY].items():
                    time = Time.from_string(time_str)
                    class_time_subdict = cls._subdict_from_json_dict(
                        time_subdict,
                        include_influencers_key=True,
                        task_history_item=task_history,
                        date_time_obj=DateTime.from_date_and_time(date, time),
                    )
                    class_times_subdict[time] = class_time_subdict
        return task_history
