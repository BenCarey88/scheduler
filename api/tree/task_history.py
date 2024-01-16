"""Class representing history of task items."""

from collections import OrderedDict
from copy import copy
from functools import partial

from scheduler.api.common.date_time import Date, DateTime, Time, TimeDelta
from scheduler.api.common.object_wrappers import HostedDataDict
from scheduler.api.common.timeline import TimelineDict
from scheduler.api.serialization import item_registry
from scheduler.api.tracker.target import target_from_dict
from scheduler.api.enums import ItemStatus, OrderedStringEnum
from scheduler.api.utils import fallback_value, print_dict, setdefault_not_none


class TaskType(OrderedStringEnum):
    """Enumeration for task types."""
    ROUTINE = "Routine"
    GENERAL = "General"


class TaskHistory(object):
    """Wrapper around a TimelineDict to represent task history.

    A task history dict is used to convey a record of the following data for
    a task over different times and dates:
        - status of the task
        - status_override of the task, ie. whether or not a specific status
            overrides statuses at previous dates and times
        - value of the task (if it has a value_type)
        - target conditions for task (set from a certain date onwards)

    It does this through a series of nested dicts, with subdicts at each
    date where some of these properties are altered, each of which contains
    further subdicts at each time where a property is altered. Properties
    set directly at date level are essentially considered to be the values
    of those properties at the end of that date, hence a value set directly
    at date level will trump any values set at times throughout that date.

    Additionally, this class uses an influencer framework to keep track of
    which objects have defined each property at each datetime, so that we can
    correctly update all properties when those influencing objects are altered.
    The influencer subdicts are used by the edit classes and shouldn't need to
    be read outside of this: the edit classes will propagate the correct
    values for each property from the influencer subdicts to the higher level
    date/time subdicts.

    The structure of a task history dict is like this:
    {
        date_1: TimelineDict({
            status: task_status,
            value: task_value,
            target: tracker_target,
            status_override: True,
            comment: comment,
            influencers: HostedDataDict({...}),
            times: TimelineDict({
                time_1: {
                    status: status_1,
                    value: value_1,
                    comment: comment_1,
                    status_override: True,
                    influencers: HostedDataDict({
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
                    }),
                },
                time_2: {
                    status: status_2,
                    value: value_2,
                    comment: comment_2,
                    influencers: HostedDataDict({...}),
                },
                ...
            }),
        }),
        ...
    }
    """
    STATUS_KEY = "status"
    VALUE_KEY = "value"
    TARGET_KEY = "target"
    COMMENT_KEY = "comment"
    INFLUENCERS_KEY = "influencers"
    TIMES_KEY = "times"
    STATUS_OVERRIDE_KEY = "status_override"
    CORE_FIELD_KEYS = [STATUS_KEY, VALUE_KEY, TARGET_KEY, STATUS_OVERRIDE_KEY]

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

    ### Core Field Getters ###
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
        # if status overridden/complete or item routine, don't check prev days
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

    def get_target_at_date(self, date):
        """Get tracker target for given date.

        Args:
            date (Date): date to get target for.

        Returns:
            (BaseTrackerTarget or None): tracker target for given date -
                this is the most recent target set before or on that date,
                if one exists.
        """
        # TODO: update other methods in this class to use the new iter_items
        # method from the TimelineDict class
        for _, subdict in self._dict.iter_items(end=date, reverse=True):
            if self.TARGET_KEY in subdict:
                return subdict[self.TARGET_KEY]
        return None

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

    # TODO: maybe add in a value_policy key for time level and date level that
    # determines if the value is a one-off/accumulates over a day/over multiple
    # days/etc.?
    def get_value_at_datetime(self, date_time):
        """Get task value at given datetime.

        Currently this works by the following logic: if there are values
        set at or before this time in the date, pick the most recent one.
        Otherwise, return None - since values are linked to routines and
        task tracking they're always assumed to reset at each date.

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
        return None

    ### Influencer Getters and Methods ###
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

    ### Edit Dict Methods ###
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
            core_field_updates (dict or None): dictionary of status, value,
                target and status overrides that the influencer will now be
                defining at the new date or time. Fields will be copied over
                from the old datetime if the influencer exists at that
                date/time, and then modified according to this dict - any
                field set to None will be deleted and any field with a defined
                value will be added or modified accordingly.

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
            core_field_updates (dict or None): dictionary of status, value,
                target and status overrides that the influencer will now be
                defining at the new date or time.
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

        # add influencer dict to diff_dict and propagate edits up to
        # times level if needed
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
        # propagate core field values from influencers at date-level first,
        # then fallback to searching for latest values from times subdict
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

        This searches for the most recent value and target and the most
        complete status after a status override, if one exists (or the most
        complete status in the dict otherwise).

        The dict being searched through will be either an influencers dict or
        a times dict, so the keys are either influencers or times, and the
        values are subdicts defining core fields (status, value, target,
        override). This is true of all the args, except for starting_values,
        which is just a core_fields dictionary.

        Args:
            dict_ (dict): ordered dict to search through.
            starting_values (dict or None): if given, use this dict to define
                the initial values of the fields - used for recursive use of
                this method only.
            diff_dict (dict(variant, dict/None) or None): diff_dict defining
                updates to core values in subdicts, to include in search.
            fallback_dict (dict or None): dict to search through if some
                fields aren't found from first one.
            fallback_diff_dict (dict(variant, dict/None) or None): diff dict
                to be used with fallback dict.

        Returns:
            (dict): dictionary defining status, value and status_override.
        """
        starting_values = starting_values or {}
        status = starting_values.get(self.STATUS_KEY, None)
        value = starting_values.get(self.VALUE_KEY, None)
        target = starting_values.get(self.TARGET_KEY)
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
            new_target = subdict.get(self.TARGET_KEY)
            new_override = subdict.get(self.STATUS_OVERRIDE_KEY)
            if (status is None or
                    (not status_override and 
                     new_status is not None and
                     new_status > status)):
                status = new_status
            if value is None and new_value is not None:
                value = new_value
            if target is None and new_target is not None:
                target = new_target
            if new_override and not status_override:
                status_override = new_override
            # break once we've found value, target and status
            if (value is not None and target is not None and
                    (status_override or status == ItemStatus.COMPLETE)):
                break

        core_fields_dict = {
            self.STATUS_KEY: status,
            self.VALUE_KEY: value,
            self.STATUS_OVERRIDE_KEY: status_override,
            self.TARGET_KEY: target,
        }
        if (fallback_dict is not None and
                (status is None or value is None or not status_override)):
            return self.__find_core_fields_dict(
                fallback_dict,
                starting_values=core_fields_dict,
                diff_dict=fallback_diff_dict,
            )
        return core_fields_dict

    ### Serialization ###
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
        keys_and_converters = [
            (self.STATUS_KEY, None),
            (self.STATUS_OVERRIDE_KEY, None),
            (self.VALUE_KEY, self._task.value_type.get_json_serializer()),
            (self.TARGET_KEY, lambda target: target.to_dict()),
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
            task,
            json_dict,
            include_influencers_key=False,
            task_history_item=None,
            date_time_obj=None):
        """Utility to get a date, time or influencer subdict from a json dict.

        Args:
            task (Task): task this history dict is for.
            json_dict (dict): json subdict to turn.
            include_influencers_key (bool): if True, also search for
                influencers key in subdict.
            task_history_item (TaskHistory): the history item being
                created.
            date_time_obj (Date or DateTime): the date time object for this
                subdict.

        Returns:
            (dict): subdict for use in class instance.
        """
        subdict = {}
        keys_and_converters = [
            (cls.STATUS_KEY, ItemStatus.from_string),
            (cls.STATUS_OVERRIDE_KEY, None),
            (cls.VALUE_KEY, task.value_type.get_json_deserializer()),
            (cls.TARGET_KEY, target_from_dict),
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
            prev_ids = []
            inf_dict_items = json_dict[cls.INFLUENCERS_KEY].items()
            for i, (id_, json_inf_subdict) in enumerate(inf_dict_items):
                # TODO this currently assumes only tasks, planned items
                # and scheduled items can be influencers. May need updating?
                # ALSO TODO: will this crash if the task influences itself
                # because it tries to add an inactive hosted data item to
                # a hosted data dict? I think it's safe based on the order
                # of things done in the task from_dict method, but should
                # keep an eye out
                prev_ids.append(id_)
                item_registry.register_callback(
                    id_,
                    partial(
                        task_history_item.__add_influencer,
                        date_time_obj,
                        cls._subdict_from_json_dict(task, json_inf_subdict),
                    ),
                    required_ids=prev_ids[:],
                    order=i,
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
                task,
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
                        task,
                        time_subdict,
                        include_influencers_key=True,
                        task_history_item=task_history,
                        date_time_obj=DateTime.from_date_and_time(date, time),
                    )
                    class_times_subdict[time] = class_time_subdict
        return task_history
