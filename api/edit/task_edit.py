"""Task edits to be applied to task items."""

from collections import OrderedDict

from scheduler.api.common.date_time import Date
from ._core_edits import AttributeEdit, CompositeEdit
from ._container_edit import DictEdit, ContainerOp


class ChangeTaskTypeEdit(AttributeEdit):
    """Task edit to change type of a task."""

    def __init__(self, task_item, new_type, register_edit=True):
        """Initialise edit.

        Args:
            task_item (Task): the task item this edit is being run on.
            new_type (TaskType): new type to change to.
            register_edit (bool): whether or not to register this edit.
        """
        super(ChangeTaskTypeEdit, self).__init__(
            {item._type: new_type for item in task_item.get_family()},
            register_edit=register_edit,
        )

        self._name = "ChangeTaskType ({0})".format(task_item.name)
        self._description = "Change task type of {0} ({1} --> {2})".format(
            task_item.path,
            task_item.type,
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
            new_status (TaskStatus or None): new status to update with.
            new_value (variant or None): value to set for task at given time.
            comment (str or None): comment to add to task history, if given.
            register_edit (bool): whether or not to register this edit.
        """
        change_status_edit = AttributeEdit(
            {task_item._status: new_status},
            register_edit=False,
        )

        history = task_item.history
        date = date_time.date()
        date_dict = OrderedDict()
        diff_dict = OrderedDict({date: date_dict})
        if new_status:
            date_dict[history.STATUS_KEY] = new_status
        if new_value:
            date_dict[history.VALUE_KEY] = new_value
        if comment:
            date_dict[history.COMMENTS_KEY] = OrderedDict({
                date_time.time(): comment
            })
        history_edit = DictEdit(
            history._dict,
            diff_dict,
            ContainerOp.ADD_OR_MODIFY,
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
