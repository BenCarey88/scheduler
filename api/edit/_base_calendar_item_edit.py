"""Edits shared between planned items and scheduled items."""

from scheduler.api.common.date_time import DateTime
from scheduler.api.utils import fallback_value

from ._core_edits import CompositeEdit, SelfInverseSimpleEdit
from ._container_edit import ListEdit, ContainerOp, ContainerEditFlag
from .task_edit import UpdateTaskHistoryEdit


# TODO use this for scheduled item edits and planned item edits in
# place of the separate ones we currently have
def _get_task_history_edits(ci, ad):
    """Get edits to update linked task history of edited calendar item.

    Args:
        ci (BaseCalendarItem): planned or scheduled item that we're editing.
        ad (dict): attribute dict, representing edits to attributes of the
            planned item.

    Returns:
        (list(UpdateTaskHistoryEdit)): list of edits to update task
            history.
    """
    edits = []

    # get old and new datetime, task and task status variables
    old_datetime = ci.end_date if ci.is_planned_item else ci.end_datetime
    old_task = ci._get_task_to_update()
    old_task_status = None
    if old_task is not None:
        old_task_status = old_task.history.get_influenced_status(
            old_datetime,
            ci,
        )
    if ci.is_planned_item:
        _new_period = (ad.get(ci._calendar_period), ci.calendar_period)
        new_datetime = _new_period.end_date
    else:
        new_datetime = DateTime.from_date_and_time(
            fallback_value(ad.get(ci._date), ci.date),
            fallback_value(ad.get(ci._end_time), ci.end_time),
        )
    new_task = ci._get_task_to_update(
        new_tree_item=ad.get(ci._tree_item),
        new_type=ad.get(ci._type),  # type is just used for scheduled items
    )
    _new_status = fallback_value(ad.get(ci._status), ci.status)
    _new_task_update_policy = fallback_value(
        ad.get(ci._task_update_policy),
        ci.task_update_policy,
    )
    new_task_status = _new_task_update_policy.get_new_status(_new_status)

    # case 1: remove from old task history and add to new task history
    if old_task != new_task:
        if old_task_status is not None:
            remove_edit = UpdateTaskHistoryEdit.create_unregistered(
                old_task,
                influencer=ci,
                old_datetime=old_datetime,
            )
            edits.append(remove_edit)
        if new_task_status is not None:
            add_edit = UpdateTaskHistoryEdit.create_unregistered(
                new_task,
                influencer=ci,
                new_datetime=new_datetime,
                new_status=new_task_status,
            )
            edits.append(add_edit)

    # case 2: update current task history
    elif (new_task_status != old_task_status or
            (new_task_status is not None and old_datetime != new_datetime)):
        remove = True if new_task_status is None else False
        task_edit = UpdateTaskHistoryEdit.create_unregistered(
            old_task,
            influencer=ci,
            old_datetime=old_datetime,
            new_datetime=new_datetime,
            new_status=new_task_status,
            remove_status=remove,
        )
        edits.append(task_edit)
    return edits


class AddCalendarItemChildRelationshipEdit(CompositeEdit):
    """Add an associated child item to a planned or scheduled item."""
    def __init__(self, parent_item, child_item):
        """Initialise edit.

        Args:
            parent_item (BaseCalendarItem): the parent item to associate to.
            child_item (BaseCalendarItem): the child item to associate.
        """
        list_edit = ListEdit.create_unregistered(
            parent_item._children,
            [child_item],
            ContainerOp.ADD,
            edit_flags=[ContainerEditFlag.LIST_IGNORE_DUPLICATES],
        )
        update_edit = SelfInverseSimpleEdit.create_unregistered(
            parent_item._update_status_from_children
        )
        subedits = [list_edit, update_edit]
        super(AddCalendarItemChildRelationshipEdit, self).__init__(
            subedits,
            validity_check_edits=[list_edit],
        )
        self._name = "AddCalendarItemChildRelationshipEdit ({0})".format(
            parent_item.name
        )
        self._description = (
            "Associate {0} {1} to {2} {3}".format(
                child_item.__class__.__name__,
                child_item.name,
                parent_item.__class__.__name__,
                parent_item.name,
            )
        )


class RemoveCalendarItemChildRelationshipEdit(CompositeEdit):
    """Remove an associated scheduled item from a planned item."""
    def __init__(self, parent_item, child_item):
        """Initialise edit.

        Args:
            parent_item (BaseCalendarItem): the parent item to remove from.
            child_item (BaseCalendarItem): the child item to remove.
        """
        list_edit = ListEdit.create_unregistered(
            parent_item._children,
            [child_item],
            ContainerOp.REMOVE,
            edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
        )
        update_edit = SelfInverseSimpleEdit.create_unregistered(
            parent_item._update_status_from_children
        )
        subedits = [list_edit, update_edit]
        super(RemoveCalendarItemChildRelationshipEdit, self).__init__(
            subedits,
            validity_check_edits=[list_edit],
        )
        self._name = "RemoveCalendarItemChildRelationshipEdit ({0})".format(
            parent_item.name
        )
        self._description = (
            "Unassociate {0} {1} from {2} {3}".format(
                child_item.__class__.__name__,
                child_item.name,
                parent_item.__class__.__name__,
                parent_item.name,
            )
        )
