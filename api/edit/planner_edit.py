"""Planner edits to be applied to planned items.

Friend classes: [PlannedItem]
"""

from scheduler.api.utils import fallback_value
from ._container_edit import ListEdit, ContainerOp, ContainerEditFlag
from ._core_edits import (
    ActivateHostedDataEdit,
    AttributeEdit,
    DeactivateHostedDataEdit,
    CompositeEdit,
)
from .task_edit import UpdateTaskHistoryEdit


def _get_task_history_edits(pi, ad):
    """Get edits to update linked task history of edited planned item.

    Args:
        pi (PlannedItem): planned item that we're editing.
        ad (dict): attribute dict, representing edits to attributes of the
            planned item.

    Returns:
        (list(UpdateTaskHistoryEdit)): list of edits to update task
            history.
    """
    edits = []

    # get old and new datetime, task and task status variables
    old_date = pi.end_date
    old_task = pi._get_task_to_update()
    old_task_status = None
    if old_task is not None:
        old_task_status = old_task.history.get_influenced_status(
            old_date,
            pi,
        )
    _new_period = (ad.get(pi._calendar_period), pi.calendar_period)
    new_date = _new_period.end_date
    new_task = pi._get_task_to_update(new_tree_item=ad.get(pi._tree_item))
    _new_status = fallback_value(ad.get(pi._status), pi.status)
    _new_task_update_policy = fallback_value(
        ad.get(pi._task_update_policy),
        pi.task_update_policy,
    )
    new_task_status = _new_task_update_policy.get_new_status(_new_status)

    # case 1: remove from old task history and add to new task history
    if old_task != new_task:
        if old_task_status is not None:
            remove_edit = UpdateTaskHistoryEdit.create_unregistered(
                old_task,
                influencer=pi,
                old_datetime=old_date,
            )
            edits.append(remove_edit)
        if new_task_status is not None:
            add_edit = UpdateTaskHistoryEdit.create_unregistered(
                new_task,
                influencer=pi,
                new_datetime=new_date,
                new_status=new_task_status,
            )
            edits.append(add_edit)

    # case 2: update current task history
    elif (new_task_status != old_task_status or
            (new_task_status is not None and old_date != new_date)):
        remove = True if new_task_status is None else False
        task_edit = UpdateTaskHistoryEdit.create_unregistered(
            old_task,
            influencer=pi,
            old_datetime=old_date,
            new_datetime=new_date,
            new_status=new_task_status,
            remove_status=remove,
        )
        edits.append(task_edit)
    return edits


class AddPlannedItemEdit(CompositeEdit):
    """Add planned item to calendar."""
    def __init__(self, planned_item, index=None, parent=None, activate=True):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): the planned item to add.
            index (int or None): index to insert at.
            parent (PlannedItem or None): parent planned item, if given.
            activate (bool): if True, activate hosted data as part of edit.
        """
        item_container = planned_item.get_item_container()
        if index is None:
            index = len(item_container)
        subedits = []
        if activate:
            subedits.append(
                ActivateHostedDataEdit.create_unregistered(planned_item)
            )
        add_edit = ListEdit.create_unregistered(
            item_container,
            [(index, planned_item)],
            ContainerOp.INSERT,
        )
        subedits.append(add_edit)
        if parent is not None:
            parent_edit = (
                AddPlannedItemChildRelationshipEdit.create_unregistered(
                    parent,
                    planned_item,
                )
            )
            if not parent_edit._is_valid:
                super(AddPlannedItemEdit, self).__init__([])
                return
            subedits.append(parent_edit)
        super(AddPlannedItemEdit, self).__init__(subedits)

        for item in item_container:
            if item.tree_item == planned_item.tree_item:
                self._is_valid = False
                return
        self._callback_args = self._undo_callback_args = [
            planned_item,
            planned_item.calendar_period,
            fallback_value(index, len(planned_item.get_item_container())),
        ]
        self._name = "AddPlannedItem ({0})".format(planned_item.name)
        self._description = (
            "Add {0} {1} to {2} at index {3}{4}".format(
                planned_item.__class__.__name__,
                planned_item.name,
                planned_item.calendar_period.name,
                str(index),
                " and make it a child of {0} {1}".format(
                    parent.__class__.__name__,
                    parent.name,
                ) if parent is not None else ""
            )
        )


class RemovePlannedItemEdit(CompositeEdit):
    """Remove planned item from calendar."""
    def __init__(self, planned_item, deactivate=True):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): planned item to remove.
            deactivate (bool): if True, deactivate hosted data as part of edit.
        """
        remove_edit = ListEdit.create_unregistered(
            planned_item.get_item_container(),
            [planned_item],
            ContainerOp.REMOVE,
            edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
        )
        subedits = [remove_edit]
        if deactivate:
            subedits.append(
                DeactivateHostedDataEdit.create_unregistered(planned_item)
            )
        # task history update - remove all influences
        for task, date in planned_item._iter_influences():
            history_removal_edit = UpdateTaskHistoryEdit.create_unregistered(
                task,
                planned_item,
                old_datetime=date,
            )
            subedits.append(history_removal_edit)
        super(RemovePlannedItemEdit, self).__init__(subedits)
        self._callback_args = self._undo_callback_args = [
            planned_item,
            planned_item.calendar_period,
            planned_item.index(),
        ]
        self._name = "RemovePlannedItem ({0})".format(planned_item.name)
        self._description = (
            "Remove {0} {1} at date {2}".format(
                planned_item.__class__.__name__,
                planned_item.name,
                planned_item.calendar_period.name,
            )
        )


class MovePlannedItemEdit(CompositeEdit):
    """Move planned item either to new period or within internal list."""
    def __init__(self, planned_item, calendar_period=None, index=None):
        """Initialise edit.

        Args:
            scheduled_item (PlannedItem): the planned item to move.
            calendar_period (CalendarPeriod or None): calendar period to
                move to, if used.
            index (int): index to move to, if used.
        """
        calendar_period_type = type(planned_item.calendar_period)
        if (not isinstance(calendar_period, (type(None), calendar_period_type))
                or (calendar_period is None and index is None)):
            super(MovePlannedItemEdit, self).__init__([])
            return

        subedits = []
        container = planned_item.get_item_container(calendar_period)
        if calendar_period is not None:
            attr_dict = {planned_item._calendar_period: calendar_period}
            attr_edit = AttributeEdit.create_unregistered(attr_dict)
            remove_edit = RemovePlannedItemEdit.create_unregistered(
                planned_item,
                deactivate=False,
            )
            if index is None:
                index = len(container)
            insert_edit = ListEdit.create_unregistered(
                container,
                [(index, planned_item)],
                ContainerOp.INSERT,
            )
            subedits = [attr_edit, remove_edit, insert_edit]
            for edit in _get_task_history_edits(planned_item, attr_dict):
                subedits.append(edit)
        else:
            move_edit = ListEdit.create_unregistered(
                container,
                [(planned_item, index)],
                ContainerOp.MOVE,
                edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
            )
            subedits = [move_edit]
        super(MovePlannedItemEdit, self).__init__(subedits)

        new_calendar_period = fallback_value(
            calendar_period,
            planned_item.calendar_period
        )
        self._callback_args = [
            planned_item,
            planned_item.calendar_period,
            planned_item.index(),
            new_calendar_period,
            index,
        ]
        self._undo_callback_args = [
            planned_item,
            new_calendar_period,
            index,
            planned_item.calendar_period,
            planned_item.index(),
        ]
        self._name = "MovePlannedItem ({0})".format(planned_item.name)
        self._description = (
            "Move {0} {1} at ({2}, row {3}) --> ({4}, row {5})".format(
                planned_item.__class__.__name__,
                planned_item.name,
                planned_item.calendar_period.name,
                planned_item.index(),
                new_calendar_period.name,
                str(index),
            )
        )


class ModifyPlannedItemEdit(CompositeEdit):
    """Modify attributes of planned item."""
    def __init__(self, planned_item, attr_dict):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): planned item to edit.
            attr_dict (dict(MutableAttribute, variant)): attributes to change.
        """
        attribute_edit = AttributeEdit.create_unregistered(attr_dict)
        subedits = [attribute_edit]
        new_calendar_period = None
        old_index = new_index = planned_item.index()

        new_calendar_period = attr_dict.get(
            planned_item._calendar_period,
            planned_item.calendar_period,
        )
        if new_calendar_period != planned_item.calendar_period:
            # remove items from old container and add to new one
            container = planned_item.get_item_container(
                new_calendar_period
            )
            new_index = len(container) - 1
            remove_edit = RemovePlannedItemEdit.create_unregistered(
                planned_item,
                deactivate=False,
            )
            add_edit = ListEdit.create_unregistered(
                container,
                [planned_item],
                ContainerOp.ADD,
            )
            subedits.extend([remove_edit, add_edit])

        # task history edits
        for edit in _get_task_history_edits(planned_item, attr_dict):
            subedits.append(edit)

        super(ModifyPlannedItemEdit, self).__init__(subedits)
        self._callback_args = [
            planned_item,
            planned_item.calendar_period,
            old_index,
            planned_item,
            new_calendar_period,
            new_index,
        ]
        self._undo_callback_args = [
            planned_item,
            new_index,
            new_calendar_period,
            planned_item,
            planned_item.calendar_period,
            old_index,
        ]
        self._name = "ModifyPlannedItem ({0})".format(planned_item.name)
        self._description = attribute_edit.get_description(
            planned_item,
            planned_item.name,
        )


class SortPlannedItemsEdit(ListEdit):
    """Sort planned items into new order."""
    def __init__(self, calendar_period, key=None, reverse=False):
        """Initialise edit.

        Args:
            calendar_period (BaseCalendarPeriod): calendar period whose planned
                items we're sorting.
            key (function or None): key to sort by.
            reverse (bool): whether or not to sort in reverse.
        """
        super(SortPlannedItemsEdit, self).__init__(
            calendar_period.get_planned_items_container(),
            [(key, reverse)],
            ContainerOp.SORT,
        )
        self._callback_args = self._undo_callback_args = [calendar_period]
        self._name = "SortPlannedItems for {0}".format(
            calendar_period.name
        )
        self._description = (
            "Rearrange order of planned items for period {0}".format(
                calendar_period.name
            )
        )
        self._edit_stack_name = "SortPlannedItems Edit Stack"

    def _stacks_with(self, edit):
        """Check if this should stack with edit if added to the log after it.

        Args:
            edit (BaseEdit): edit to check if this should stack with.

        Returns:
            (bool): True if other edit is also same class as this one, else
                False.
        """
        return isinstance(edit, SortPlannedItemsEdit)


class AddScheduledItemChildRelationshipEdit(ListEdit):
    """Add an associated scheduled item to a planned item."""
    def __init__(self, scheduled_item, planned_item):
        """Initialise edit.

        Args:
            scheduled_item (ScheduledItem): the scheduled item to associate.
            planned_item (PlannedItem): the planned item to associate to.
        """
        super(AddScheduledItemChildRelationshipEdit, self).__init__(
            planned_item._scheduled_items,
            [scheduled_item],
            ContainerOp.ADD,
        )
        self._name = "AddScheduledItemChildRelationshipEdit ({0})".format(
            scheduled_item.name
        )
        self._description = (
            "Associate {0} {1} to {2} {3}".format(
                scheduled_item.__class__.__name__,
                scheduled_item.name,
                planned_item.__class__.__name__,
                planned_item.name,
            )
        )


class RemoveScheduledItemChildRelationshipEdit(ListEdit):
    """Remove an associated scheduled item from a planned item."""
    def __init__(self, scheduled_item, planned_item):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): the planned item to remove from.
            scheduled_item (ScheduledItem): the scheduled item to remove.
        """
        super(RemoveScheduledItemChildRelationshipEdit, self).__init__(
            planned_item._scheduled_items,
            [scheduled_item],
            ContainerOp.REMOVE,
            edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
        )
        self._name = "RemoveScheduledItemChildRelationshipEdit ({0})".format(
            planned_item.name
        )
        self._description = (
            "Unassociate {0} {1} from {2} {3}".format(
                scheduled_item.__class__.__name__,
                scheduled_item.name,
                planned_item.__class__.__name__,
                planned_item.name,
            )
        )


class AddPlannedItemChildRelationshipEdit(ListEdit):
    """Add an associated planned item child to a planned item."""
    def __init__(self, planned_item, planned_item_child):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): the planned item to add to.
            planned_item_child (PlannedItem): the planned item child to add.
        """
        super(AddPlannedItemChildRelationshipEdit, self).__init__(
            planned_item._planned_children,
            [planned_item_child],
            ContainerOp.ADD,
        )
        self._is_valid = (planned_item_child < planned_item)
        self._name = "AddPlannedItemChildRelationship ({0})".format(
            planned_item.name
        )
        self._description = (
            "Make {0} {1} a child to {2} {3}".format(
                planned_item_child.__class__.__name__,
                planned_item_child.name,
                planned_item.__class__.__name__,
                planned_item.name,
            )
        )


class RemovePlannedItemChildRelationshipEdit(ListEdit):
    """Remove an associated planned item child from a planned item."""
    def __init__(self, planned_item, planned_item_child):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): the planned item to remove from.
            planned_item_child (PlannedItem): the planned item child to remove.
        """
        super(RemovePlannedItemChildRelationshipEdit, self).__init__(
            planned_item._planned_children,
            planned_item,
            ContainerOp.REMOVE,
            edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
        )
        self._name = "RemovePlannedItemChildRelationship from ({0})".format(
            planned_item.name
        )
        self._description = (
            "Remove {0} {1} as child of {2} {3}".format(
                planned_item_child.__class__.__name__,
                planned_item_child.name,
                planned_item.__class__.__name__,
                planned_item.name,
            )
        )
