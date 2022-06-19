"""Planner edits to be applied to planned items.

Friend classes: [PlannedItem]
"""

from scheduler.api.common.object_wrappers import MutableHostedAttribute
from ._container_edit import ListEdit, ContainerOp, ContainerEditFlag
from ._core_edits import AttributeEdit, CompositeEdit


class AddPlannedItemEdit(ListEdit):
    """Add planned item to calendar."""
    def __init__(self, planned_item, index=None):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): the planned item to add.
            index (int or None): index to insert at.
        """
        item_container = planned_item.get_item_container()
        if index is None:
            index = len(item_container)
        super(AddPlannedItemEdit, self).__init__(
            item_container,
            [(index, planned_item)],
            ContainerOp.INSERT,
        )
        self._name = "AddPlannedItem ({0})".format(planned_item.name)
        self._description = (
            "Add {0} {1} to {2} at index {3}".format(
                planned_item.__class__.__name__,
                planned_item.name,
                planned_item.calendar_period.name,
                str(index),
            )
        )


class RemovePlannedItemEdit(ListEdit):
    """Remove planned item from calendar."""
    def __init__(self, planned_item):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): planned item to remove.
        """
        super(RemovePlannedItemEdit, self).__init__(
            planned_item.get_item_container(),
            [planned_item],
            ContainerOp.REMOVE,
            edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
        )
        self._name = "RemovePlannedItem ({0})".format(planned_item.name)
        self._description = (
            "Remove {0} {1} at date {2}".format(
                planned_item.__class__.__name__,
                planned_item.name,
                planned_item.calendar_period.name,
            )
        )


class MovePlannedItemEdit(ListEdit):
    """Move planned item in internal list."""
    def __init__(self, planned_item, index):
        """Initialise edit.

        Args:
            scheduled_item (PlannedItem): the planned item to move.
            index (int): index to move to.
        """
        super(MovePlannedItemEdit, self).__init__(
            planned_item.get_item_container(),
            [(planned_item, index)],
            ContainerOp.MOVE,
            edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
        )
        self._name = "MovePlannedItem ({0})".format(planned_item.name)
        self._description = (
            "Move {0} {1} at date {2} to index {3}".format(
                planned_item.__class__.__name__,
                planned_item.name,
                planned_item.calendar_period.name,
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
        if planned_item._calendar_period in attr_dict:
            new_calendar_period = attr_dict[planned_item._calendar_period]
            # remove items from old container and add to new one
            remove_edit = RemovePlannedItemEdit.create_unregistered(
                planned_item
            )
            add_edit = ListEdit.create_unregistered(
                planned_item.get_item_container(new_calendar_period),
                [planned_item],
                ContainerOp.ADD,
            )
            subedits.extend([remove_edit, add_edit])

        super(ModifyPlannedItemEdit, self).__init__(subedits)
        self._name = "ModifyPlannedItem ({0})".format(planned_item.name)
        self._description = attribute_edit.get_description(
            planned_item,
            planned_item.name
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


class SchedulePlannedItemEdit(ListEdit):
    """Add an associated scheduled item to a planned item."""
    def __init__(self, planned_item, scheduled_item):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): the planned item to associate to.
            scheduled_item (ScheduledItem): the scheduled item to associate.
        """
        super(SchedulePlannedItemEdit, self).__init__(
            planned_item._scheduled_items,
            [MutableHostedAttribute(scheduled_item)],
            ContainerOp.ADD,
        )
        self._name = "SchedulePlannedItem ({0})".format(planned_item.name)
        self._description = (
            "Schedule {0} {1} for {2} {3}".format(
                scheduled_item.__class__.__name__,
                scheduled_item.name,
                planned_item.__class__.__name__,
                planned_item.name,
            )
        )


class UnschedulePlannedItemEdit(ListEdit):
    """Remove an associated scheduled item from a planned item."""
    def __init__(self, planned_item, scheduled_item):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): the planned item to remove from.
            scheduled_item (ScheduledItem): the scheduled item to remove.
        """
        # note that we need to remove by index as the attribute is mutable
        index = planned_item.scheduled_items.index(scheduled_item)
        super(UnschedulePlannedItemEdit, self).__init__(
            planned_item._scheduled_items,
            [index],
            ContainerOp.REMOVE,
        )
        self._name = "UnschedulePlannedItem ({0})".format(planned_item.name)
        self._description = (
            "Unschedule {0} {1} from {2} {3}".format(
                scheduled_item.__class__.__name__,
                scheduled_item.name,
                planned_item.__class__.__name__,
                planned_item.name,
            )
        )


class AddPlannedItemChild(ListEdit):
    """Add an associated planned item child to a planned item."""
    def __init__(self, planned_item, planned_item_child,):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): the planned item to add to.
            planned_item_child (PlannedItem): the planned item child to add.
        """
        super(AddPlannedItemEdit, self).__init__(
            planned_item._planned_children,
            [planned_item_child],
            ContainerOp.ADD,
        )
        self._name = "AddPlannedItemChild to ({0})".format(planned_item.name)
        self._description = (
            "Add {0} {1} to {2} {3}".format(
                planned_item_child.__class__.__name__,
                planned_item_child.name,
                planned_item.__class__.__name__,
                planned_item.name,
            )
        )


class RemovePlannedItemChild(ListEdit):
    """Remove an associated planned item child from a planned item."""
    def __init__(self, planned_item, planned_item_child,):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): the planned item to remove from.
            planned_item_child (PlannedItem): the planned item child to remove.
        """
        super(RemovePlannedItemChild, self).__init__(
            planned_item._planned_children,
            [planned_item_child],
            ContainerOp.ADD,
        )
        self._name = "AddPlannedItemChild to ({0})".format(planned_item.name)
        self._description = (
            "Add {0} {1} to {2} {3}".format(
                planned_item_child.__class__.__name__,
                planned_item_child.name,
                planned_item.__class__.__name__,
                planned_item.name,
            )
        )
