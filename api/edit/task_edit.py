"""Task edits to be applied to task items."""

from collections import OrderedDict

from scheduler.api.common.date_time import Date
from ._core_edits import CompositeEdit, SelfInverseSimpleEdit
from ._ordered_dict_edit import OrderedDictEdit, OrderedDictOp


class ChangeTaskTypeEdit(SelfInverseSimpleEdit):
    """Task edit to change type of a task."""

    def __init__(self, task_item, new_type, register_edit=True):
        """Initialise edit.

        Args:
            task_item (Task): the task item this edit is being run on.
            new_type (TaskType): new type to change to.
            register_edit (bool): whether or not to register this edit.
        """
        orig_type = task_item.type
        def _change_type(object_to_edit, inverse):
            object_to_edit.type = orig_type if inverse else new_type
        super(ChangeTaskTypeEdit, self).__init__(
            task_item,
            run_func=_change_type,
            register_edit=register_edit,
        )

        self._name = "ChangeTaskType ({0})".format(task_item.name)
        self._description = "Change task type of {0} ({1} --> {2})".format(
            task_item.path,
            orig_type,
            new_type,
        )


class UpdateTaskHistoryEdit(CompositeEdit):
    """Edit to update task history."""

    def __init__(
            self,
            task_item,
            date_time,
            new_status=None,
            new_value=None,
            comment=None,
            register_edit=True):
        """Initialise base tree edit.

        Args:
            task_item (Task): the task item this edit is being run on.
            date_time (DateTime): time that the update is being made.
            new_status (TaskStatusor None): new status to update with.
            new_value (variant): value to set for task at given time.
            comment (str or None): comment to add to task history, if given.
            register_edit (bool): whether or not to register this edit.
        """
        orig_status = task_item.status
        def _change_status(object_to_edit, inverse):
            object_to_edit.status = orig_status if inverse else new_status
        change_status_edit = SelfInverseSimpleEdit(
            task_item,
            run_func=_change_status,
            register_edit=False,
        )

        history = task_item.history
        date = str(date_time.date())
        # TODO: decide if this conversion of datetime to string belongs here
        # or in task_history class. Task history class is probably better but
        # found the function a faff to write - what we really want is a way to
        # copy the dict and iterate through it to convert all date_times to
        # strings but ignore everything else (and vice versa for other way)
        date_dict = OrderedDict()
        diff_dict = OrderedDict({date: date_dict})
        if new_status:
            date_dict[history.STATUS_KEY] = new_status
        if new_value:
            date_dict[history.VALUE_KEY] = new_value
        if comment:
            date_dict[history.COMMENTS_KEY] = OrderedDict({
                str(date_time.time()): comment
            })
        history_edit = OrderedDictEdit(
            ordered_dict=history.dict,
            diff_dict=diff_dict,
            op_type=OrderedDictOp.ADD_OR_MODIFY,
            recursive=True,
            register_edit=False,
        )

        # For now, we only update task status if this is for current date
        # TODO: this logic is gross though tbh, and not really accurate for
        # what we want. This should probably just be broken into two different
        # edits (one for task status, one for history)
        if date_time.date() == Date.now():
            super(UpdateTaskHistoryEdit, self).__init__(
                [change_status_edit, history_edit],
                register_edit=register_edit,
            )
        else:
            super(UpdateTaskHistoryEdit, self).__init__(
                [history_edit],
                register_edit=register_edit,
            )
        self._is_valid = bool(new_value or new_status or comment)
        self._name = "UpdateTaskHistory ({0})".format(task_item.name)

        update_texts = []
        if new_status:
            update_texts.append(
                "status ({0} --> {1})".format(orig_status, new_status)
            )
        # TODO: give task history a get method so we don't have to go
        # through the dict
        orig_value = history.dict.get(date, {}).get(history.VALUE_KEY)
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
