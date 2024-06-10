"""Edits to be applied to task and task category items."""

# from collections import OrderedDict
from functools import partial

from scheduler.api.common.date_time import Date, DateTime
from ._base_edit import EditError
from ._core_edits import AttributeEdit, CompositeEdit, SelfInverseSimpleEdit
from ._container_edit import DictEdit, ContainerEditFlag, ContainerOp, ListEdit
from .tree_edit import RenameChildrenEdit


class ModifyTaskEdit(CompositeEdit):
    """Task edit to change attributes of a task."""
    def __init__(self, task_item, attr_dict, is_task=True, tracker=None):
        """Initialise edit.

        Args:
            task_item (BaseTaskItem): the task item this edit is being run on.
            attr_dict (dict(MutableAttribute, variant)): attributes to update.
            is_task (bool): if True, this item is a task (and not a category)
                and so has more attributes that can be updated.
            tracker (Tracker or None): tracker class - needed for changing
                is_tracked state of tasks.
        """
        subedits = []

        # type edits apply to whole family
        # TODO: THEY SHOULDN'T! REMOVE THIS
        if is_task and task_item._type in attr_dict:
            new_type = attr_dict[task_item._type]
            attr_dict.update(
                {item._type: new_type for item in task_item.get_family()}
            )

        # if we change is_tracked, we need to add to/remove from tracker as well
        if (is_task
                and task_item._is_tracked in attr_dict
                and attr_dict[task_item._is_tracked] != task_item.is_tracked):
            if tracker is None:
                raise EditError(
                    "Cannot edit task_item tracking properties without "
                    "supplying tracker arg"
                )
            add_tracking = attr_dict.get(task_item._is_tracked)
            add_or_remove_task_edit = ListEdit.create_unregistered(
                tracker._tracked_tasks,
                [task_item],
                ContainerOp.ADD if add_tracking else ContainerOp.REMOVE,
                edit_flags=[
                    ContainerEditFlag.LIST_IGNORE_DUPLICATES,
                    ContainerEditFlag.LIST_FIND_BY_VALUE,
                ],
            )
            subedits.append(add_or_remove_task_edit)

        # rename edits need to rename item in parent dict as well
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
                the edit will add the updates as a new influencer instead.
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
            "value: {3}, target: {4})".format(
                task_item.path,
                new_datetime,
                new_status,
                new_value,
                str(new_target),
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


# TODO: make these inherit from the modify_task edit above?
# might need to think a bit about callbacks for both though as ideally this
# would need to trigger 2 separate callbacks (one for tracker modifying and
# one for tasks, but there may be an issue with using both at once, may need
# to instead split up into an add_or_remove_to_tracker edit and task_attr_edit)
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
