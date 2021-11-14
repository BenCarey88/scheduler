"""Task edits to be applied to task items."""

from collections import OrderedDict

from ._base_edit import SelfInverseSimpleEdit
from ._composite_edit import CompositeEdit
from ._ordered_dict_edit import OrderedDictEdit, OrderedDictOp


class ChangeTaskType(SelfInverseSimpleEdit):
    """Task edit to change type of a task."""

    def __init__(self, task_item, new_type, register_edit=True):
        """Initialise edit.

        Args:
            task_item (Task): the task item this edit is being run on.
            new_type (TaskType): new type to change to.
            register_edit (bool): whether or not to register this edit.
        """
        self.task_item = task_item
        self.original_type = task_item.type
        self.new_type = new_type
        super(ChangeTaskType, self).__init__(
            task_item,
            register_edit=register_edit,
        )
        self._name = "ChangeTaskType ({0})".format(task_item.name)
        self._description = "Change task type of {0} ({1} --> {2})".format(
            task_item.path,
            self.original_type,
            self.new_type,
        )

    def _run_func(self, task_item, inverse):
        """Change type of task item.

        Args:
            task_item (Task): the task item to be edited.
            inverse (bool): whether we're using for _run or inverse _run.
        """
        task_type = self.original_type if inverse else self.new_type
        task_item.type = task_type


class ChangeTaskStatus(SelfInverseSimpleEdit):
    """Task edit to change status of a task."""

    def __init__(self, task_item, new_status, register_edit):
        """Initialise edit.

        Args:
            task_item (Task): the task item this edit is being run on.
            new_status (TaskStatus): new status to change to.
            register_edit (bool): whether or not to register this edit.
        """
        self.task_item = task_item
        self.original_status = task_item.status
        self.new_status = new_status
        super(ChangeTaskStatus, self).__init__(
            task_item,
            register_edit=register_edit,
        )

    def _run_func(self, task_item, inverse):
        """Change status of task item.

        Args:
            task_item (Task): the task item to be edited.
            inverse (bool): whether we're using for _run or inverse _run.
        """
        status = self.original_status if inverse else self.new_status
        task_item.status = status


class UpdateTaskHistory(CompositeEdit):
    """Edit to update task history."""

    def __init__(self, task_item, datetime, new_status, register_edit=True):
        """Initialise base tree edit.

        Args:
            task_item (Task): the task item this edit is being run on.
            datetime (datetime.datetime): time that the update is being made.
            new_status (TaskStatus): new status to update with.
            register_edit (bool): whether or not to register this edit.
        """
        def _change_status(_task_item, _inverse):
            _task_item.status = task_item.status if _inverse else new_status
        change_status_edit = SelfInverseSimpleEdit(
            task_item,
            run_func=_change_status,
            register_edit=False,
        )

        history_edit = OrderedDictEdit(
            ordered_dict=task_item.history.dict,
            diff_dict=OrderedDict([()]),
            op_type=OrderedDictOp.ADD,
            register_edit=False,
        )

        ordered
        super(UpdateTaskHistory, self).__init__(
            [tree_item, tree_item._children]
            [name_change_edit, ordered_dict_edit],
            register_edit=register_edit,
        )
