"""Task edits to be applied to task items."""

from collections import OrderedDict

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
            self.original_type,
            self.new_type,
        )


class UpdateTaskHistoryEdit(CompositeEdit):
    """Edit to update task history."""

    def __init__(
            self,
            task_item,
            date_time,
            new_status,
            comment=None,
            register_edit=True):
        """Initialise base tree edit.

        Args:
            task_item (Task): the task item this edit is being run on.
            date_time (datetime.datetime): time that the update is being made.
            new_status (TaskStatus): new status to update with.
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
        date = date_time.date()
        diff_dict = OrderedDict({
            date: OrderedDict({
                history.STATUS_KEY: new_status
            })
        })
        if comment:
            diff_dict[date][history.COMMENTS_KEY] = OrderedDict({
                date_time.time(): comment
            })
        history_edit = OrderedDictEdit(
            ordered_dict=history.dict,
            diff_dict=diff_dict,
            op_type=OrderedDictOp.ADD,
            recursive=True,
            register_edit=False,
        )

        super(UpdateTaskHistoryEdit, self).__init__(
            [change_status_edit, history_edit],
            register_edit=register_edit,
        )
