"""Task class."""

from collections import OrderedDict

from scheduler.api.common.date_time import Date, DateTime, Time, TimeDelta
from scheduler.api.common.object_wrappers import (
    HostedDataDict,
    MutableAttribute,
)
from scheduler.api.common.timeline import TimelineDict
from scheduler.api.serialization.serializable import SaveType
from scheduler.api.constants import ItemStatus
from scheduler.api.utils import OrderedStringEnum

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
        return self.history.get_status_at_datetime(DateTime.now())

        # I'm changing this to just find status at the current datetime, as it
        # needs to update as the time changes.
        # TODO: keep an eye on if this seems to slow stuff down considerably.
        # there's definitely stuff I can do with caching to speed it up
        # TODO: delete below when I'm more confident, and delete the
        # _status attribute, plus its corresponding logic in the to_dict
        # and from_dict methods
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


class TaskHistory(object):
    """Simple wrapper around an OrderedDict to represent task history.

    The structure of a task history dict is like this:
    {
        date_1: {
            status: task_status,
            value: task_value,
            latest_time: time_n,
            times: {
                time_1: {
                    status: status_1,
                    value: value_1,
                    comment: comment_1,
                    influencers: {
                        influencer_1: {
                            status: status_1.1,
                            value: value_1.1,
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
    LATEST_TIME_KEY = "latest_time"

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

    # def get_status_at_date(self, date, end=False):
    #     """Get task status at given date.

    #     This will just return the status specified at the given date, if
    #     it exists, otherwise it will find the most recently specified date.
    #     If nothing is specified before this date, it defaults to unstarted.
    #     Note that this DOESN'T attempt to look at the time subdictionary.
    #     It is the responsibility of any edit that alters the time subdict
    #     to also propagate any status changes up to the current date.

    #     Args:
    #         date (Date): date to query.

    #     Returns:
    #         (ItemStatus): task status at given date.
    #     """
    #     status = self.get_dict_at_date(date).get(self.STATUS_KEY)
    #     if status:
    #         return status
    #     if self._task.type != TaskType.ROUTINE:
    #         # if task isn't routine, default to last recorded status
    #         for recorded_date, subdict in reversed(self._dict.items()):
    #             if recorded_date < date and self.STATUS_KEY in subdict:
    #                 return subdict[self.STATUS_KEY]
    #     return ItemStatus.UNSTARTED

    def get_status_at_end_of_date(self, date):
        """Get task status by end of given date.

        This will just return the status specified by the STATUS key at the
        given date if it exists, as this represents the latest status at
        that date. If it doesn't exist, this will return the status at the
        start of the date, as determined by the function below.

        Note that this DOESN'T attempt to look at the time subdictionary.
        It is the responsibility of any edit that alters the time subdict
        to also propagate any status changes up to the current date.
        Crucially this means that we CAN'T use this function as part of
        the logic for the _update_date_dict_from_time method.

        Args:
            date (Date): date to query.

        Returns:
            (ItemStatus): task status at given date.
        """
        status = self.get_dict_at_date(date).get(self.STATUS_KEY)
        if status:
            return status
        return self.get_status_at_start_of_date(date)

    def get_status_at_start_of_date(self, date):
        """Get task status at the start of given date.

        For routines this will always be unstarted. For non-routines,
        this is just the most recent status before the current date
        (defaulting to unstarted).

        Args:
            date (Date): date to query.

        Returns:
            (ItemStatus): task status at start of given date.
        """
        if self._task.type != TaskType.ROUTINE:
            # if task isn't routine, default to last recorded status
            for recorded_date in reversed(self._dict):
                subdict = self._dict[recorded_date]
                if recorded_date < date and self.STATUS_KEY in subdict:
                    return subdict[self.STATUS_KEY]
        return ItemStatus.UNSTARTED

    def get_status_at_date(self, date):
        """Get task status at the end of given date.

        TODO: This is here for backwards compatibility. It should be removed
        soon once all its uses are replaced with get_status_at_end_of_date.
        OR: we should keep? I don't know. Maybe want to go back to being
        able to set directly at dates and just interpreting it as end of
        dates?

        Args:
            date (Date): date to query.

        Returns:
            (ItemStatus): task status at start of given date.
        """
        return self.get_status_at_end_of_date(date)

    # TODO: make this match the corresponding status methods?
    def get_value_at_date(self, date):
        """Get task value at given date.

        Args:
            date (Date): date to query.

        Returns:
            (variant or None): task value at given date, if set.
        """
        return self.get_dict_at_date(date).get(self.VALUE_KEY, None)

    def get_status_at_datetime(self, date_time):
        """Get task status at given datetime.

        Currently this works by the following logic: if there are statuses
        set at or before this time in the date, pick the most recent one.
        Otherwise, find the status set at the date of the previous day.
        Statuses on the current day are considered to be completed at the
        very end of the day, so won't apply to a datetime within the day.

        Args:
            date_time (DateTime): datetime to query.

        Returns:
            (ItemStatus): task status at given datetime.
        """
        date_dict = self.get_dict_at_date(date_time.date())
        times_dict = date_dict.get(self.TIMES_KEY, {})
        for time in reversed(times_dict):
            subdict = times_dict.get(time)
            if self.STATUS_KEY in subdict and time <= date_time.time():
                return subdict[self.STATUS_KEY]
        return self.get_status_at_start_of_date(date_time.date())

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
        return self.get_value_at_date(
            date_time.date() - TimeDelta(days=1)
        )

    # TODO: this doesn't work for undos - use gets instead and then implement
    # as an edit
    # def _update_task_status(self):
    #     """Update task status to reflect today's date history.

    #     This is intended to be used by edit classes only, as it modifies the
    #     value of the task status mutable attribute.

    #     Returns:
    #         (bool): whether or not status was changed.
    #     """
    #     status = self.get_status_at_date(Date.now())
    #     if status != self._task.status:
    #         # global_influencers = self._task._history_influencers.get(
    #         #     self._task.GLOBAL_INFLUENCER
    #         # )
    #         # if global_influencers:
    #         #     influenced_status = global_influencers.get(
    #         #         self._task.STATUS_KEY
    #         #     )
    #         #     if influenced_status >= status:
    #         #         return False
    #         self._task._status.set_value(status)
    #         return True
    #     return False

    # def _update_task_at_date(self, date):
    #     """Update task at date to match time dict at that date.

    #     This is intended to be used by edit classes only.

    #     Args:
    #         date (Date): date to update at.

    #     Returns:
    #         (bool): whether or not any updates were made.
    #     """
    #     date_dict = self.get_dict_at_date(date)
    #     if date_dict is None:
    #         # if nothing exists at date, there's nothing to update
    #         return False
    #     # if self._task._history_influencers.get(date):
    #     #     # if there is an influencer for this date, just use that
    #     #     return False

    #     value_set = False
    #     status_set = False
    #     times_dict = date_dict.get(self.TIMES_KEY, {})
    #     for _, subdict in reversed(times_dict.items()):
    #         if not value_set and self.VALUE_KEY in subdict:
    #             date_dict[self.VALUE_KEY] = subdict[self.VALUE_KEY]
    #             value_set = True
    #         if not status_set and self.STATUS_KEY in subdict:
    #             date_dict[self.STATUS_KEY] = subdict[self.STATUS_KEY]
    #             status_set = True
    #     return status_set or value_set

    def get_influencers_dict(self, date_time):
        """Get influencers dict for given datetime.

        Args:
            date_time (DateTime): date time to check.

        Returns:
            (HostedDataDict): influencers dict.
        """
        time_dict = self.get_dict_at_datetime(date_time)
        return time_dict.get(self.INFLUENCERS_KEY, {})

    def get_influenced_status(self, date_time, influencer):
        """Get status defined by given influencer at given datetime, if exists.

        Args:
            date_time (DateTime): date time to check.
            influencer (variant): item to check.

        Returns:
            (ItemStatus or None): status, if found.
        """
        influencers_dict = self.get_influencers_dict(date_time)
        return influencers_dict.get(influencer, {}).get(self.STATUS_KEY)

    def get_influenced_value(self, date_time, influencer):
        """Get value defined by given influencer at given datetime, if exists.

        Args:
            date_time (DateTime): date time to check.
            influencer (variant): item to check.

        Returns:
            (variant or None): value, if found.
        """
        influencers_dict = self.get_influencers_dict(date_time)
        return influencers_dict.get(influencer, {}).get(self.VALUE_KEY)

    # TODO: THIS CAUSES CRASHES - FIX
    #
    # This does some cleanup on the dictionary, deleting unnecessary bits,
    # but that means we get crashes, for example in the following scenario:
    #   - edit removes an influencer from a time dict, triggering cleanup
    #   - cleanup deletes a time dict because that was the only influencer
    #   - inverse edit is now assuming that the dict will look the same and
    #       so has an inverse_diff_dict that matches the old structure
    #   - this inverse_diff_dict no longer matches the new structure and
    #       crashes when it attempts to do an insert but can't go far enough
    #       down the nesting
    #
    # to fix this, we could:
    #   a) remove the deletion stuff. I don't like this solution though as
    #       we do want to delete things or the dict will be quite messy?
    #       probably the easiest option though. I guess we're safe to delete
    #       anything except the influencer dicts, but this means maintaining
    #       essentially empty timeline dicts of no longer relevant times
    #   b) make this function a getter that returns a diff_dict, so we can
    #       do the update properly as an edit. This is a better option, BUT:
    #       we could have some deletion and some addition to do? Not certain,
    #       but if we do then we need to ensure these are returned as separate
    #       dicts so we can do 2 separate edits with them. Either way, this
    #       needs to make it clear when returning whether the edit should be
    #       deletion or insertion.
    #   MAIN PROBLEM HERE: the getter won't be up to date when we use it goddamn
    #   so I guess we would need to also pass in all the relevant changes to
    #   consider, ie. influencers we're going to remove/add at each time. So
    #   we'll basically need to port all of UpdateTaskHistoryEdit's args
    #   into here, in which case may as well also return the diff dicts computed
    #   there too. So basically can have a function get_diff_dicts() which
    #   returns one large diff_dict for a remove edit and one large diff_dict
    #   for an add_or_modify edit, then do remove first and then add
    #
    def _update_from_influencers(self, date_time, update_date_dict=True):
        """Update status and values based on influencers at datetime.

        This is intended to be used by edit classes only.

        Args:
            date_time (DateTime): datetime to update at.
            update_date_dict (bool): if True, also propagate updates up to
                date dict. This is included to allow us to skip this update
                in an edit that is already doing it elsewhere.
        """
        date = date_time.date()
        time = date_time.time()
        time_dict = self.get_dict_at_datetime(date_time)
        date_dict = self.get_dict_at_date(date)
        times_dict = date_dict.get(self.TIMES_KEY, {})

        # update time_dict status and value from influencers at that time
        status_set = False
        value_set = False
        influencers_dict = time_dict.get(self.INFLUENCERS_KEY, {})
        for influencer in reversed(influencers_dict):
            influencer_dict = influencers_dict[influencer]
            if self.STATUS_KEY in influencer_dict:
                status = influencer_dict.get(self.STATUS_KEY)
                if not status_set or status > status_set:
                    # use most complete status if multiple exist
                    time_dict[self.STATUS_KEY] = status
                    status_set = status
            if not value_set and self.VALUE_KEY in influencer_dict:
                value = influencer_dict.get(self.VALUE_KEY)
                time_dict[self.VALUE_KEY] = value
                value_set = True
            if value_set and status_set == ItemStatus.COMPLETE:
                break
        else:
            # delete status or value if no influencer is setting them
            if not status_set and self.STATUS_KEY in time_dict:
                del time_dict[self.STATUS_KEY]
            if not value_set and self.VALUE_KEY in time_dict:
                del time_dict[self.VALUE_KEY]
            # delete time dict if neither status nor value is set
            # (cause 1 of above mentioned crash)
            if not (status_set or value_set) and time in times_dict:
                del times_dict[time]

        # then update date dict from time dict
        if update_date_dict:
            self._update_date_dict_from_times(date)

    def _update_date_dict_from_times(self, date):
        """Update date dict based on time subdict.

        Args:
            date (Date): date to update at.
        """
        date_dict = self.get_dict_at_date(date)
        time_dict = date_dict.get(self.TIMES_KEY, TimelineDict())

        # set latest time
        latest_time = time_dict.latest_key()
        if latest_time and date_dict.get(self.LATEST_TIME_KEY) != latest_time:
            date_dict[self.LATEST_TIME_KEY] = latest_time

        # update status and values to latest defined or delete if not there
        status_set = False
        value_set = False
        for time in reversed(time_dict):
            time_subdict = time_dict.get(time)
            if not status_set and self.STATUS_KEY in time_subdict:
                date_dict[self.STATUS_KEY] = time_subdict.get(self.STATUS_KEY)
                status_set = True
            if not value_set and self.VALUE_KEY in time_subdict:
                date_dict[self.VALUE_KEY] = time_subdict.get(self.VALUE_KEY)
                value_set = True
            if value_set and status_set:
                break
        else:
            # delete status or value if not set in subdict
            if not status_set and self.STATUS_KEY in date_dict:
                del date_dict[self.STATUS_KEY]
            if not value_set and self.VALUE_KEY in date_dict:
                del date_dict[self.VALUE_KEY]
            # delete times subdict if we're not setting a status or value
            # note that we can't delete the date dict as it may go out of
            # sync with the corresponding date dict in the global history
            if not (status_set or value_set):
                if self.TIMES_KEY in date_dict:
                    # cause 2 of above mentioned crash
                    del date_dict[self.TIMES_KEY]
                if self.LATEST_TIME_KEY in date_dict:
                    del date_dict[self.LATEST_TIME_KEY]

    # def _get_diff_dict_at_date(self, date, update_from_time=True):
    #     """Get diff dict for a given date based on the time dict.

    #     This is intended to be used by edit classes. It returns a dict
    #     defining any new status that should be set at date level based
    #     on its influencers and time subdict. The logic first ensures
    #     that the status is set to whatever the latest influencer sets
    #     it to, then overrides this with the time value so long as this
    #     is greater than the influencer.

    #     Args:
    #         date (Date): date to check at.
    #         update_from_time (bool): if True, allow overrides from the
    #             time subdict. Otherwise only base on influencers.

    #     Returns:
    #         (dict): diff dict.
    #     """
    #     date_dict = self.get_dict_at_date(date)
    #     if date_dict is None:
    #         # if nothing exists at date, there's nothing to update
    #         return {}

    #     # influenced status is status set by most recent influencer
    #     new_status = None
    #     status = date_dict.get(self.STATUS_KEY)
    #     influenced_status = None
    #     influences_dict = date_dict.get(self.INFLUENCERS_KEY, {})
    #     for _, subdict in reversed(influences_dict.items()):
    #         if self.STATUS_KEY in subdict:
    #             influenced_status = subdict[self.STATUS_KEY]
    #     if influenced_status and status != influenced_status:
    #         new_status = influenced_status

    #     # new time status is latest status in time dict
    #     if update_from_time:
    #         time_status = None
    #         times_dict = date_dict.get(self.TIMES_KEY, {})
    #         for _, subdict in reversed(times_dict.items()):
    #             if self.STATUS_KEY in subdict:
    #                 time_status = subdict[self.STATUS_KEY]
    #                 if not new_status or time_status > new_status:
    #                     new_status = time_status
    #                     new_influencers = 
    #                 break

    #     if new_status and new_status != status:
    #         return {self.STATUS_KEY: new_status}
    #     return None

    def to_dict(self):
        """Convert class to serialized json dict.

        In practice, this just converts the Date and Time objects to strings.

        Returns:
            (OrderedDict): json dict.
        """
        json_dict = OrderedDict()
        for date, subdict in self._dict.items():
            json_subdict = {}
            if self.STATUS_KEY in subdict:
                json_subdict[self.STATUS_KEY] = subdict[self.STATUS_KEY]
            if self.VALUE_KEY in subdict:
                json_subdict[self.VALUE_KEY] = subdict[self.VALUE_KEY]
            if self.COMMENT_KEY in subdict:
                json_subdict[self.COMMENT_KEY] = subdict[self.COMMENT_KEY]
            if self.TIMES_KEY in subdict:
                json_times_subdict = OrderedDict()
                json_subdict[self.TIMES_KEY] = json_times_subdict
                for time, time_subdict in subdict[self.TIMES_KEY].items():
                    json_times_subdict[time.string()] = OrderedDict(
                        time_subdict
                    )
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
        class_dict = TimelineDict()
        for date, subdict in json_dict.items():
            class_subdict = {}
            class_dict[Date.from_string(date)] = class_subdict
            if cls.STATUS_KEY in subdict:
                class_subdict[cls.STATUS_KEY] = subdict[cls.STATUS_KEY]
            if cls.VALUE_KEY in subdict:
                class_subdict[cls.VALUE_KEY] = subdict[cls.VALUE_KEY]
            if cls.COMMENT_KEY in subdict:
                class_subdict[cls.COMMENT_KEY] = subdict[cls.COMMENT_KEY]
            if cls.TIMES_KEY in subdict:
                class_times_subdict = TimelineDict()
                class_subdict[cls.TIMES_KEY] = class_times_subdict
                for time, time_subdict in subdict[cls.TIMES_KEY].items():
                    class_times_subdict[Time.from_string(time)] = OrderedDict(
                        time_subdict
                    )
        task_history = cls(task)
        task_history._dict = class_dict
        return task_history
