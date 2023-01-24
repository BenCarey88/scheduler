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


class UpdateTaskHistoryEdit(CompositeEdit):
    """Edit to update task history."""
    def __init__(
            self,
            task_item,
            date,
            time=None,
            new_status=None,
            new_value=None,
            comment=None,
            influencer=None):
        """Initialise edit.

        Args:
            task_item (Task): the task item this edit is being run on.
            date (Date): date to update at.
            time (Time or None): time to update at, if given.
            new_status (ItemStatus or None): new status to update with.
            new_value (variant or None): value to set for task at given time.
            comment (str or None): comment to add to task history, if given.
        """
        self.task_item = task_item
        history = task_item.history

        datetime_dict = OrderedDict()
        if new_status:
            datetime_dict[history.STATUS_KEY] = new_status
        if new_value:
            datetime_dict[history.VALUE_KEY] = new_value
        if comment:
            datetime_dict[history.COMMENT_KEY] = comment

        if time is None:
            diff_dict = TimelineDict({date: datetime_dict})
        else:
            diff_dict = TimelineDict(
                {date: {history.TIMES_KEY: datetime_dict}}
            )

        history_edit = DictEdit.create_unregistered(
            history._dict,
            diff_dict,
            ContainerOp.ADD_OR_MODIFY,
            recursive=True,
        )
        update_task_edit = SelfInverseSimpleEdit.create_unregistered(
            history._update_task_status,
        )
        subedits = [history_edit, update_task_edit]
        if time is not None:
            # if doing a time edit, then update history at that date
            update_date_edit = SelfInverseSimpleEdit.create_unregistered(
                partial(history._update_task_at_date, date)
                # TODO: create this function
            )
            subedits.insert(1, update_date_edit)
        if not history.get_dict_at_date(date):
            # add to root history data dict too if not been added yet
            global_history_edit = SelfInverseSimpleEdit.create_unregistered(
                partial(
                    task_item.root._history_data._update_for_task,
                    date,
                    task_item,
                )
            )
            subedits.append(global_history_edit)

        # We need to not reverse order for inverse because update_task and
        # global_history edits both rely on the history edit being done/undone
        # first.
        super(UpdateTaskHistoryEdit, self).__init__(
            subedits,
            reverse_order_for_inverse=False,
        )
        # TODO: use validity_check_edits __init__ arg instead
        # of setting is_valid explicitly - just need to make sure
        # the ContainerEdit is_valid logic works for recursive edits
        self._is_valid = (
            new_value != task_item.get_value_at_date(date)
            or new_status != task_item.get_status_at_date(date)
            or comment is not None
        )
        self._callback_args = self._undo_callback_args = [(
            task_item,
            task_item,
        )]
        self._name = "UpdateTaskHistory ({0})".format(task_item.name)

        update_texts = []
        orig_status = history.get_status_at_date(date)
        orig_value = history.get_value_at_date(date)
        if new_status:
            update_texts.append(
                "status ({0} --> {1})".format(orig_status, new_status)
            )
        if new_value:
            update_texts.append(
                "value ({0} --> {1})".format(str(orig_value), str(new_value))
            )
        update_text = ", ".join(update_texts)

        self._description = (
            "Update task history for {0} at date {1}{2}".format(
                task_item.path,
                date,
                " - {0}".format(update_text) if update_text else ""
            )
        )


# Replace UpdateTaskHistoryEdit with this new UpdateHistoryEdit

class UpdateHistoryEdit(CompositeEdit):
    """Edit to update task history at given date or time."""
    def __init__(
            self,
            task_item,
            datetime=None,
            new_status=None,
            new_value=None,
            comment=None,
            influencer=None):
        """Initialise edit.

        Args:
            task_item (Task): the task item this edit is being run on.
            datetime (Date, DateTime or None): the date or datetime to update
                at. [If not given, we update globally.?]
            new_datetime (Date, DateTime or None): the date or datetime that
                this influencer will now be influencing at. If not given, the
                edit will remove the influencer instead.
            new_status (ItemStatus or None):  new status to update with.
            new_value (variant or None): value to set for task at given time.
            comment (str or None): comment to add to task history, if given.
            influencer (variant or None): the object that is influencing the
                status update, if given.
        """


class UpdateStatusInfluencerEdit(CompositeEdit):
    """Edit to update a status history influencer for a task."""
    def __init__(
            self,
            task_item,
            influencer,
            old_status=None,
            new_status=None,
            old_datetime=None,
            new_datetime=None):
        """Initialise edit.

        Args:
            task_item (Task): the task whose status is being influenced.
            influencer (variant): the object that is influencing the status.
            old_status (ItemStatus or None): the status that the influencer
                was setting. If None, the influencer is being added.
            new_status (ItemStatus or None): the status that the influencer
                will be setting. If None, the influencer is being removed.
            old_datetime (Date, DateTime or None): the date or datetime that
                this influencer was previously influencing at. If not given,
                the edit will add it as a new influencer instead.
            new_datetime (Date, DateTime or None): the date or datetime that
                this influencer will now be influencing at. If not given, the
                edit will remove the influencer instead.
        """
        history = task_item.history
        subedits = []

        # remove old status at old date/time
        if old_status is not None and old_datetime is not None:
            if isinstance(old_datetime, Date):
                remove_diff_dict = TimelineDict({
                    old_datetime: {
                        history.STATUS_INFLUENCERS_KEY: {
                            old_status: HostedDataList([influencer])
                        }
                    }
                })
            elif isinstance(old_datetime, DateTime):
                remove_diff_dict = TimelineDict({
                    old_datetime.date(): {
                        history.TIMES_KEY: TimelineDict({
                            old_datetime.time(): {
                                history.STATUS_INFLUENCERS_KEY: {
                                    old_status: HostedDataList([influencer])
                                }
                            }
                        })
                    }
                })
            else:
                raise EditError("old_datetime arg must be a Date or DateTime")
            remove_edit = DictEdit.create_unregistered(
                history._dict,
                remove_diff_dict,
                ContainerOp.REMOVE,
                recursive=True,
                edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
            )
            subedits.append(remove_edit)

        # add new status at new date/time
        if new_status is not None and new_datetime is not None:
            if isinstance(new_datetime, Date):
                add_diff_dict = TimelineDict({
                    new_datetime: {
                        history.STATUS_INFLUENCERS_KEY: {
                            new_status: HostedDataList([influencer])
                        }
                    }
                })
            elif isinstance(old_datetime, DateTime):
                add_diff_dict = TimelineDict({
                    new_datetime.date(): {
                        history.TIMES_KEY: TimelineDict({
                            new_datetime.time(): {
                                history.STATUS_INFLUENCERS_KEY: {
                                    new_status: HostedDataList([influencer])
                                }
                            }
                        })
                    }
                })
            else:
                raise EditError("new_datetime arg must be a Date or DateTime")
            add_edit = DictEdit.create_unregistered(
                history._dict,
                add_diff_dict,
                ContainerOp.ADD,
                recursive=True,
            )
            subedits.append(add_edit)

        update_status_edit = SelfInverseSimpleEdit.create_unregistered(
            history._update_task_status,
        )
        subedits.append(update_status_edit)

        super(UpdateStatusInfluencerEdit, self).__init__(
            subedits,
            reverse_order_for_inverse=False,
        )
        self._is_valid = self._is_valid and (
            old_status != new_status or
            old_datetime != new_datetime
        )
