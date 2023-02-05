"""Task edits to be applied to task items."""

from collections import OrderedDict
from functools import partial

from scheduler.api.common.date_time import Date, DateTime
from scheduler.api.common.object_wrappers import HostedDataDict, HostedDataList
from scheduler.api.common.timeline import TimelineDict
from ._base_edit import EditError
from ._core_edits import AttributeEdit, CompositeEdit, SelfInverseSimpleEdit
from ._container_edit import DictEdit, ContainerEditFlag, ContainerOp


class ModifyTaskEdit(AttributeEdit):
    """Task edit to change attributes of a task."""
    def __init__(self, task_item, attr_dict):
        """Initialise edit.

        Args:
            task_item (Task): the task item this edit is being run on.
            attr_dict (dict(MutableAttribute, variant)): attributes to update.
            new_type (TaskType): new type to change to.
        """
        # type edits apply to whole family
        # TODO: THEY SHOULDN'T!
        if task_item._type in attr_dict:
            new_type = attr_dict[task_item._type]
            attr_dict.update(
                {item._type: new_type for item in task_item.get_family()}
            )
        super(ModifyTaskEdit, self).__init__(attr_dict)
        self._callback_args = self._undo_callback_args = [(
            task_item,
            task_item,
        )]
        self._name = "ModifyTask ({0})".format(task_item.name)
        self._description = self.get_description(
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


class UpdateTaskHistoryEdit(CompositeEdit):
    """Edit to update history for a task."""
    def __init__(
            self,
            task_item,
            influencer,
            old_datetime=None,
            new_datetime=None,
            new_status=None,
            new_value=None):
        """Initialise edit.

        Args:
            task_item (Task): the task which is being updated.
            influencer (variant): the object that is influencing the update.
            old_datetime (DateTime or None): the datetime that this influencer
                was previously influencing at. If not given, the edit will add
                it as a new influencer instead.
            new_datetime (Date, DateTime or None): the datetime that this
                update will be occurring at. If not given, the edit will just
                remove the influencer at the old time instead.
            new_status (ItemStatus or None): the status that the influencer
                will now be setting, if given.
            new_value (variant or None): the new value that the influencer will
                now be setting, if given.
        """
        history = task_item.history
        subedits = []
        new_updates = (new_status is not None or new_value is not None)
        keep_last_for_inverse = []

        # remove influencer at old date/time if it's different to new one
        if (old_datetime is not None and
                (old_datetime != new_datetime or not new_updates)):
            influencers_dict = history.get_influencers_dict(old_datetime)
            if influencer in influencers_dict:
                remove_diff_dict = TimelineDict({
                    old_datetime.date(): {
                        history.TIMES_KEY: TimelineDict({
                            old_datetime.time(): {
                                history.INFLUENCERS_KEY: HostedDataDict({
                                    influencer: None
                                })
                            }
                        })
                    }
                })
                remove_edit = DictEdit.create_unregistered(
                    history._dict,
                    remove_diff_dict,
                    ContainerOp.REMOVE,
                    recursive=True,
                )
                # propagate updates upwards
                update_date_dict = (
                    new_datetime is None
                    or old_datetime.date() != new_datetime.date()
                    or not new_updates
                )
                # ^ only update date dict if not being done later
                update_edit = SelfInverseSimpleEdit.create_unregistered(
                    partial(
                        history._update_from_influencers,
                        old_datetime,
                        update_date_dict=update_date_dict,
                    )
                )
                subedits.extend([remove_edit, update_edit])

                # update root history data dict too in case needs deleting
                global_edit = SelfInverseSimpleEdit.create_unregistered(
                    partial(
                        task_item.root._history_data._update_for_task,
                        old_datetime.date(),
                        task_item,
                    )
                )
                subedits.append(global_edit)
                keep_last_for_inverse.append(global_edit)

        # add (or modify) influencer at new date/time
        if new_datetime is not None and new_updates:
            influencer_dict = {}
            if new_status is not None:
                influencer_dict[history.STATUS_KEY] = new_status
            if new_value is not None:
                influencer_dict[history.VALUE_KEY] = new_value
            add_diff_dict = TimelineDict({
                new_datetime.date(): {
                    history.TIMES_KEY: TimelineDict({
                        new_datetime.time(): {
                            history.INFLUENCERS_KEY: HostedDataDict({
                                influencer: influencer_dict
                            })
                        }
                    })
                }
            })
            add_edit = DictEdit.create_unregistered(
                history._dict,
                add_diff_dict,
                ContainerOp.ADD_OR_MODIFY,
                recursive=True,
            )
            # propagate updates upwards
            update_edit = SelfInverseSimpleEdit.create_unregistered(
                partial(
                    history._update_from_influencers,
                    new_datetime,
                )
            )
            subedits.extend([add_edit, update_edit])

            # add to root history data dict too if not been added yet
            if not history.get_dict_at_date(new_datetime.date()):
                global_edit = SelfInverseSimpleEdit.create_unregistered(
                    partial(
                        task_item.root._history_data._update_for_task,
                        new_datetime.date(),
                        task_item,
                    )
                )
                subedits.append(global_edit)
                keep_last_for_inverse.append(global_edit)

        super(UpdateTaskHistoryEdit, self).__init__(
            subedits,
            keep_last_for_inverse=keep_last_for_inverse,
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
