"""Edits to be applied to task and task category items."""

# from collections import OrderedDict
from functools import partial

from scheduler.api.common.date_time import Date, DateTime
# from scheduler.api.common.object_wrappers import HostedDataDict, HostedDataList
# from scheduler.api.common.timeline import TimelineDict
# from ._base_edit import EditError
from ._core_edits import AttributeEdit, CompositeEdit, SelfInverseSimpleEdit
from ._container_edit import DictEdit, ContainerEditFlag, ContainerOp, ListEdit
from .tree_edit import RenameChildrenEdit


class ModifyTaskEdit(CompositeEdit):
    """Task edit to change attributes of a task."""
    def __init__(self, task_item, attr_dict, is_task=True):
        """Initialise edit.

        Args:
            task_item (BaseTaskItem): the task item this edit is being run on.
            attr_dict (dict(MutableAttribute, variant)): attributes to update.
            is_task (bool): if True, this item is a task (and not a category)
                and so has more attributes that can be updated.
        """
        subedits = []
        # type edits apply to whole family
        # TODO: THEY SHOULDN'T!
        if is_task and task_item._type in attr_dict:
            new_type = attr_dict[task_item._type]
            attr_dict.update(
                {item._type: new_type for item in task_item.get_family()}
            )
        # rename in parent dict as well if needed
        if task_item._name in attr_dict:
            name = attr_dict[task_item._name]
            parent = task_item.parent
            if parent is not None and not parent.get_child(name):
                name_edit = RenameChildrenEdit.create_unregistered(
                    parent,
                    {task_item.name: name},
                    dict_edit_only=True,
                )
                subedits.append(name_edit)
            else:
                # can't change name if other child with new name exists
                del attr_dict[task_item._name]
        attr_edit = AttributeEdit.create_unregistered(attr_dict)
        subedits.insert(0, attr_edit)
        super(ModifyTaskEdit, self).__init__(subedits)
        self._callback_args = self._undo_callback_args = [(
            task_item,
            task_item,
        )]
        self._name = "ModifyTaskItem ({0})".format(task_item.name)
        self._description = attr_edit.get_description(
            task_item,
            task_item.name,
        )


# class UpdateTaskHistoryEdit(CompositeEdit):
#     """Edit to update task history."""
#     def __init__(
#             self,
#             task_item,
#             date,
#             time=None,
#             new_status=None,
#             new_value=None,
#             comment=None,
#             influencer=None):
#         """Initialise edit.

#         Args:
#             task_item (Task): the task item this edit is being run on.
#             date (Date): date to update at.
#             time (Time or None): time to update at, if given.
#             new_status (ItemStatus or None): new status to update with.
#             new_value (variant or None): value to set for task at given time.
#             comment (str or None): comment to add to task history, if given.
#         """
#         self.task_item = task_item
#         history = task_item.history

#         datetime_dict = OrderedDict()
#         if new_status:
#             datetime_dict[history.STATUS_KEY] = new_status
#         if new_value:
#             datetime_dict[history.VALUE_KEY] = new_value
#         if comment:
#             datetime_dict[history.COMMENT_KEY] = comment

#         if time is None:
#             diff_dict = TimelineDict({date: datetime_dict})
#         else:
#             diff_dict = TimelineDict(
#                 {date: {history.TIMES_KEY: datetime_dict}}
#             )

#         history_edit = DictEdit.create_unregistered(
#             history._dict,
#             diff_dict,
#             ContainerOp.ADD_OR_MODIFY,
#             recursive=True,
#         )
#         # update_task_edit = SelfInverseSimpleEdit.create_unregistered(
#         #     history._update_task_status,
#         # )
#         subedits = [history_edit] #, update_task_edit]
#         if time is not None:
#             # if doing a time edit, then update history at that date
#             update_date_edit = SelfInverseSimpleEdit.create_unregistered(
#                 partial(history._update_task_at_date, date)
#                 # TODO: create this function
#             )
#             subedits.insert(1, update_date_edit)
#         if not history.get_dict_at_date(date):
#             # add to root history data dict too if not been added yet
#             global_history_edit = SelfInverseSimpleEdit.create_unregistered(
#                 partial(
#                     task_item.root._history_data._update_for_task,
#                     date,
#                     task_item,
#                 )
#             )
#             subedits.append(global_history_edit)

#         # We need to not reverse order for inverse because update_task and
#         # global_history edits both rely on the history edit being done/undone
#         # first.
#         super(UpdateTaskHistoryEdit, self).__init__(
#             subedits,
#             reverse_order_for_inverse=False,
#         )
#         # TODO: use validity_check_edits __init__ arg instead
#         # of setting is_valid explicitly - just need to make sure
#         # the ContainerEdit is_valid logic works for recursive edits
#         self._is_valid = (
#             new_value != task_item.get_value_at_date(date)
#             or new_status != task_item.get_status_at_date(date)
#             or comment is not None
#         )
#         self._callback_args = self._undo_callback_args = [(
#             task_item,
#             task_item,
#         )]
#         self._name = "UpdateTaskHistory ({0})".format(task_item.name)

#         update_texts = []
#         orig_status = history.get_status_at_date(date)
#         orig_value = history.get_value_at_date(date)
#         if new_status:
#             update_texts.append(
#                 "status ({0} --> {1})".format(orig_status, new_status)
#             )
#         if new_value:
#             update_texts.append(
#                 "value ({0} --> {1})".format(str(orig_value), str(new_value))
#             )
#         update_text = ", ".join(update_texts)

#         self._description = (
#             "Update task history for {0} at date {1}{2}".format(
#                 task_item.path,
#                 date,
#                 " - {0}".format(update_text) if update_text else ""
#             )
#         )


# class UpdateTaskHistoryEdit(CompositeEdit):
#     """Edit to update task history at given date or time."""
#     def __init__(
#             self,
#             task_item,
#             influencer,
#             date_time,
#             new_status=None,
#             new_value=None):
#         """Initialise edit.

#         Args:
#             task_item (Task): the task item this edit is being run on.
#             influencer (variant): the object that is influencing the status
#                 update.
#             date_time (DateTime): datetime to update at.
#             new_status (ItemStatus or None):  new status to update with.
#             new_value (variant or None): value to set for task at given time.
#         """
#         self.task_item = task_item
#         history = task_item.history
#         date = date_time.date()
#         time = date_time.time()

#         # update history dict at given datetime
#         time_diff_dict = OrderedDict()
#         if new_status:
#             time_diff_dict[history.STATUS_KEY] = new_status
#         if new_value:
#             time_diff_dict[history.VALUE_KEY] = new_value

#         diff_dict = TimelineDict({
#             date: {history.TIMES_KEY: TimelineDict({time: time_diff_dict})}
#         })
#         history_edit = DictEdit.create_unregistered(
#             history._dict,
#             diff_dict,
#             ContainerOp.ADD_OR_MODIFY,
#             recursive=True,
#         )
#         subedits = [history_edit]

#         # add influencer edit
#         old_status = history.get_influenced_status(date_time, influencer)
#         influencer_edit = UpdateStatusInfluencerEdit.create_unregistered(
#             task_item,
#             influencer,
#             old_status,
#             new_status,
#             date_time,
#             date_time,
#             propagate_updates=False,
#         )
#         subedits.append(influencer_edit)

#         # propagate updates from time dict up to date dict
#         update_date_dict_edit = SelfInverseSimpleEdit.create_unregistered(
#             partial(history._update_date_dict_from_times, date)
#         )
#         subedits.append(update_date_dict_edit)

#         # add to root history data dict too if not been added yet
#         if not history.get_dict_at_date(date):
#             global_history_edit = SelfInverseSimpleEdit.create_unregistered(
#                 partial(
#                     task_item.root._history_data._update_for_task,
#                     date,
#                     task_item,
#                 )
#             )
#             subedits.append(global_history_edit)

#         # We need to not reverse order for inverse because global_history
#         # edit relies on the history edit being done first.
#         super(UpdateTaskHistoryEdit, self).__init__(
#             subedits,
#             reverse_order_for_inverse=False,
#         )
#         # TODO: use validity_check_edits __init__ arg instead
#         # of setting is_valid explicitly - just need to make sure
#         # the ContainerEdit is_valid logic works for recursive edits
#         self._is_valid = (
#             new_value != task_item.get_value_at_date(date)
#             or new_status != task_item.get_status_at_date(date)
#             or comment is not None
#         )
#         self._callback_args = self._undo_callback_args = [(
#             task_item,
#             task_item,
#         )]
#         self._name = "UpdateTaskHistory ({0})".format(task_item.name)

#         update_texts = []
#         orig_status = history.get_status_at_datetime(date_time)
#         orig_value = history.get_value_at_date(date)
#         if new_status:
#             update_texts.append(
#                 "status ({0} --> {1})".format(orig_status, new_status)
#             )
#         if new_value:
#             update_texts.append(
#                 "value ({0} --> {1})".format(str(orig_value), str(new_value))
#             )
#         update_text = ", ".join(update_texts)

#         self._description = (
#             "Update task history for {0} at datetime {1}{2}".format(
#                 task_item.path,
#                 date_time,
#                 " - {0}".format(update_text) if update_text else ""
#             )
#         )


# TODO:
# a better way to organise this is basically just the dict update does
#   - the comment at given time
#   - the status influencers
#   - the value influencers
#       (this is just OderedDict of influencers and values, latest wins)
# then we do function edit to set status and value from influencer fields
# and then another function to propagate those up to date
# so everything is controlled from the influencer fields
#
# this means that UpdateStatusInfluencerEdit does most of the work and
# we can remove the propagate_updates kwaarg because we always want it
# but we will need to add the value logic in order to do this

# ^^^ I THINK THIS CAN BE IGNORED AND ALL THE ABOVE CAN BE DELETED NOW


class UpdateTaskHistoryEdit(CompositeEdit):
    """Edit to update history for a task."""
    def __init__(
            self,
            task_item,
            influencer,
            old_datetime=None,
            new_datetime=None,
            new_status=None,
            new_value=None,
            new_target=None,
            new_status_override=None,
            remove_status=False,
            remove_value=False,
            remove_target=False,
            remove_status_override=False):
        """Initialise edit.

        Args:
            task_item (Task): the task which is being updated.
            influencer (Hosted): the object that is influencing the update -
                note that this can just be the task item itself.
            old_datetime (Date, DateTime or None): the date or datetime that
                this influencer was previously influencing at. If not given,
                the edit will add it as a new influencer instead.
            new_datetime (Date, DateTime or None): the date or datetime that
                this update will be occurring at. If not given, the edit will
                just remove the influencer at the old time instead.
            new_status (ItemStatus or None): the status that the influencer
                will now be setting, if given.
            new_value (variant or None): the new value that the influencer will
                now be setting, if given.
            new_target ((BaseTrackerTarget or None): target value to set from
                the given date, if wanted.
            new_status_override (BaseTrackerTarget or None):
            remove_status (bool): if True, remove status from influencer.
            remove_value (bool): if True, remove value from influencer.
            remove_target (bool): if True, remove target at old date.
            remove_status_override (bool): if True, remove status override.
        """
        history = task_item.history
        core_field_updates = {}
        keys_and_args = {
            history.STATUS_KEY: (new_status, remove_status),
            history.VALUE_KEY: (new_value, remove_value),
            history.STATUS_OVERRIDE_KEY: (
                new_status_override, remove_status_override
            ),
            history.TARGET_KEY: (new_target, remove_target),
        }
        for key, (add_arg, remove_arg) in keys_and_args.items():
            if remove_arg:
                core_field_updates[key] = None
            elif add_arg is not None:
                core_field_updates[key] = add_arg

        # dictionary edit to update history dict
        diff_dict = history._get_update_edit_diff_dict(
            influencer,
            old_datetime,
            new_datetime,
            core_field_updates,
        )
        if diff_dict is None:
            super(UpdateTaskHistoryEdit, self).__init__([])
            return
        dict_edit = DictEdit.create_unregistered(
            history._dict,
            diff_dict,
            ContainerOp.ADD_REMOVE_OR_MODIFY,
            recursive=True,
        )

        # add to root history data dict too
        dates = []
        for date_time_obj in (old_datetime, new_datetime):
            if isinstance(date_time_obj, DateTime):
                dates.append(date_time_obj.date())
            elif isinstance(date_time_obj, Date):
                dates.append(date_time_obj)
        global_edit = SelfInverseSimpleEdit.create_unregistered(
            partial(
                task_item.root._history_data._update_for_task_at_dates,
                task_item,
                dates,
            )
        )

        super(UpdateTaskHistoryEdit, self).__init__(
            [dict_edit, global_edit],
            reverse_order_for_inverse=False,
        )
        # TODO: work out extra _is_valid conditions
        self._callback_args = self._undo_callback_args = [(
            task_item,
            task_item,
        )]
        self._name = "UpdateTaskHistory ({0})".format(task_item.name)
        self._description = (
            "Update task history for {0} at datetime {1} (status: {2}, "
            "value: {3})".format(
                task_item.path,
                new_datetime,
                new_status,
                new_value,
            )
        )


class ClearTaskHistoryEdit(DictEdit):
    """Clear task history dict."""
    def __init__(self, task_item):
        """Initialize edit.

        Args:
            task_item (Task): task to clear history of.
        """
        history_dict = task_item.history._dict
        diff_dict = {date: None for date in history_dict}
        super(ClearTaskHistoryEdit, self).__init__(
            history_dict,
            diff_dict,
            ContainerOp.REMOVE,
        )
        self._callback_args = self._undo_callback_args = [(
            task_item,
            task_item,
        )]
        self._name = "ClearTaskHistory ({0})".format(task_item.name)
        self._description = (
            "Clear task history for {0}".format(task_item.path)
        )


class TrackTaskEdit(CompositeEdit):
    """Edit to add task to tracker."""
    def __init__(self, task_item, tracker):
        """Initialize edit.

        Args:
            task_item (Task): task to add to tracker.
            tracker (Tracker): the tracker object to add to.
        """
        add_task_edit = ListEdit.create_unregistered(
            tracker._tracked_tasks,
            [task_item],
            ContainerOp.ADD,
            edit_flags=[ContainerEditFlag.LIST_IGNORE_DUPLICATES],
        )
        attr_edit = AttributeEdit.create_unregistered(
            {task_item._is_tracked: True}
        )
        super(TrackTaskEdit, self).__init__([add_task_edit, attr_edit])
        #TODO: create tracker modify callback and add this edit to it
        self._callback_args = self._undo_callback_args = [(
            task_item,
            task_item,
        )]
        self._name = "TrackTaskEdit ({0})".format(task_item.name)
        self._description = (
            "Add task {0} to tracker".format(task_item.path)
        )


class UntrackTaskEdit(CompositeEdit):
    """Edit to add task to tracker."""
    def __init__(self, task_item, tracker):
        """Initialize edit.

        Args:
            task_item (Task): task to add to tracker.
            tracker (Tracker): the tracker object to add to.
        """
        remove_task_edit = ListEdit.create_unregistered(
            tracker._tracked_tasks,
            [task_item],
            ContainerOp.REMOVE,
            edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
        )
        attr_edit = AttributeEdit.create_unregistered(
            {task_item._is_tracked: True}
        )
        super(UntrackTaskEdit, self).__init__([remove_task_edit, attr_edit])
        #TODO: create tracker modify callback and add this edit to it
        self._callback_args = self._undo_callback_args = [(
            task_item,
            task_item,
        )]
        self._name = "UntrackTaskEdit ({0})".format(task_item.name)
        self._description = (
            "Remove task {0} from tracker".format(task_item.path)
        )
