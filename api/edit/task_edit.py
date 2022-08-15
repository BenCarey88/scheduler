"""Task edits to be applied to task items."""

from collections import OrderedDict
from functools import partial

from scheduler.api.common.date_time import Date
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
            date_time,
            new_status=None,
            new_value=None,
            comment=None):
        """Initialise base tree edit.

        Args:
            task_item (Task): the task item this edit is being run on.
            date_time (DateTime): time that the update is being made.
            new_status (TaskStatus or None): new status to update with.
            new_value (variant or None): value to set for task at given time.
            comment (str or None): comment to add to task history, if given.
        """
        self.task_item = task_item
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
