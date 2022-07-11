"""Planner edits to be applied to planned items.

Friend classes: [PlannedItem]
"""

# TODO: delete the commented out MutableHostedAttributes
# from scheduler.api.common.object_wrappers import MutableHostedAttribute
from scheduler.api.utils import fallback_value
from ._container_edit import ListEdit, ContainerOp, ContainerEditFlag
from ._core_edits import AttributeEdit, CompositeEdit, RemoveFromHostEdit


class AddPlannedItemEdit(CompositeEdit):
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
        add_edit = ListEdit.create_unregistered(
            item_container,
            [(index, planned_item)],
            ContainerOp.INSERT,
        )
        subedits = [add_edit]
        tree_item_container = planned_item.get_tree_item_container()
        if tree_item_container is not None:
            tree_attr_edit = ListEdit.create_unregistered(
                tree_item_container,
                [planned_item],
                # [MutableHostedAttribute(planned_item)],
                ContainerOp.ADD,
            )
            subedits.append(tree_attr_edit)
        super(AddPlannedItemEdit, self).__init__(subedits)

        self._callback_args = self._undo_callback_args = [
            planned_item,
            planned_item.calendar_period,
            index,
        ]
        self._name = "AddPlannedItem ({0})".format(planned_item.name)
        self._description = (
            "Add {0} {1} to {2} at index {3}".format(
                planned_item.__class__.__name__,
                planned_item.name,
                planned_item.calendar_period.name,
                str(index),
            )
        )


class RemovePlannedItemEdit(CompositeEdit):
    """Remove planned item from calendar."""
    def __init__(self, planned_item, remove_host=True):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): planned item to remove.
            remove_host (bool): if True, we remove host as part of edit
        """
        remove_edit = ListEdit.create_unregistered(
            planned_item.get_item_container(),
            [planned_item],
            ContainerOp.REMOVE,
            edit_flags=[ContainerEditFlag.LIST_FIND_BY_VALUE],
        )
        subedits = [remove_edit]
        if remove_host:
            remove_from_host_edit = RemoveFromHostEdit.create_unregistered(
                planned_item,
            )
            subedits.append(remove_from_host_edit)
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
            attr_edit = AttributeEdit.create_unregistered(
                {planned_item._calendar_period: calendar_period}
            )
            remove_edit = RemovePlannedItemEdit.create_unregistered(
                planned_item,
                remove_host=False,
            )
            if index is None:
                index = len(container)
            insert_edit = ListEdit.create_unregistered(
                container,
                [(index, planned_item)],
                ContainerOp.INSERT,
            )
            subedits = [attr_edit, remove_edit, insert_edit]
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
                remove_host=False,
            )
            add_edit = ListEdit.create_unregistered(
                container,
                [planned_item],
                ContainerOp.ADD,
            )
            subedits.extend([remove_edit, add_edit])

        new_tree_item = attr_dict.get(
            planned_item._tree_item,
            planned_item.tree_item
        )
        if new_tree_item != planned_item.tree_item:
            # change old and new tree item's planned_item args
            old_container = planned_item.get_tree_item_container()
            new_container = planned_item.get_tree_item_container(new_tree_item)
            tree_remove_edit = ListEdit.create_unregistered(
                old_container,
                [planned_item],
                # [MutableHostedAttribute(planned_item)],
                ContainerOp.REMOVE,
            )
            tree_add_edit = ListEdit.create_unregistered(
                new_container,
                [],
                ContainerOp.ADD,
            )
            subedits.extend([tree_remove_edit, tree_add_edit])

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


class AddScheduledItemChildRelationshipEdit(CompositeEdit):
    """Add an associated scheduled item to a planned item."""
    def __init__(self, scheduled_item, planned_item):
        """Initialise edit.

        Args:
            scheduled_item (ScheduledItem): the scheduled item to associate.
            planned_item (PlannedItem): the planned item to associate to.
        """
        if (scheduled_item in planned_item.scheduled_items
                or planned_item in scheduled_item.planned_items):
            super(AddScheduledItemChildRelationshipEdit, self).__init__([])
            self._is_valid = False
            return
        child_edit = ListEdit.create_unregistered(
            planned_item._scheduled_items,
            [scheduled_item],
            # [MutableHostedAttribute(scheduled_item)],
            ContainerOp.ADD,
        )
        parent_edit = ListEdit.create_unregistered(
            scheduled_item._planned_items,
            [planned_item],
            # [MutableHostedAttribute(planned_item)],
            ContainerOp.ADD,
        )
        super(AddScheduledItemChildRelationshipEdit, self).__init__(
            [child_edit, parent_edit]
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


class RemoveScheduledItemChildRelationshipEdit(CompositeEdit):
    """Remove an associated scheduled item from a planned item."""
    def __init__(self, scheduled_item, planned_item):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): the planned item to remove from.
            scheduled_item (ScheduledItem): the scheduled item to remove.
        """
        if (scheduled_item not in planned_item.scheduled_items
                or planned_item not in scheduled_item.planned_items):
            super(RemoveScheduledItemChildRelationshipEdit, self).__init__([])
            self._is_valid = False
            return
        # note that we need to remove by index as the attribute is mutable
        child_index = planned_item.scheduled_items.index(scheduled_item)
        parent_index = scheduled_item.planned_items.index(planned_item)

        child_edit = ListEdit.create_unregistered(
            planned_item._scheduled_items,
            [child_index],
            ContainerOp.REMOVE,
        )
        parent_edit = ListEdit.create_unregistered(
            scheduled_item._planned_items,
            [parent_index],
            ContainerOp.REMOVE,
        )
        super(RemoveScheduledItemChildRelationshipEdit, self).__init__(
            [child_edit, parent_edit]
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


class AddPlannedItemChildRelationshipEdit(CompositeEdit):
    """Add an associated planned item child to a planned item."""
    def __init__(self, planned_item, planned_item_child):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): the planned item to add to.
            planned_item_child (PlannedItem): the planned item child to add.
        """
        if (planned_item_child >= planned_item
                or planned_item_child in planned_item.planned_children):
            super(AddPlannedItemChildRelationshipEdit, self).__init__([])
            self._is_valid = False
            return
        child_edit = ListEdit.create_unregistered(
            planned_item._planned_children,
            [planned_item_child],
            # [MutableHostedAttribute(planned_item_child)],
            ContainerOp.ADD
        )
        parent_edit = ListEdit.create_unregistered(
            planned_item_child._planned_parents,
            [planned_item],
            # [MutableHostedAttribute(planned_item)],
            ContainerOp.ADD,
        )
        super(AddPlannedItemChildRelationshipEdit, self).__init__(
            [child_edit, parent_edit]
        )
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


class RemovePlannedItemChildRelationshipEdit(CompositeEdit):
    """Remove an associated planned item child from a planned item."""
    def __init__(self, planned_item, planned_item_child):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): the planned item to remove from.
            planned_item_child (PlannedItem): the planned item child to remove.
        """
        parent_index = planned_item.parent_index(planned_item_child)
        child_index = planned_item_child.child_index(planned_item)
        if (parent_index is None or child_index is None):
            super(RemovePlannedItemChildRelationshipEdit, self).__init__([])
            self._is_valid = False
            return

        # note that we need to remove by index as the attribute is mutable
        child_edit = ListEdit.create_unregistered(
            planned_item._planned_children,
            child_index,
            ContainerOp.REMOVE,
        )
        parent_edit = ListEdit.create_unregistered(
            planned_item._planned_parents,
            parent_index,
            ContainerOp.REMOVE,
        )
        super(RemovePlannedItemChildRelationshipEdit, self).__init__(
            [child_edit, parent_edit]
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


class AddPlannedItemAsChildEdit(CompositeEdit):
    """Create planned item and make it a child of the given parent."""
    def __init__(self, planned_item, planned_item_parent, index=None):
        """Initialise edit.

        Args:
            planned_item (PlannedItem): the planned item to add.
            planned_item_parent (PlannedItem): the planned item to set as
                its parent.
        """
        child_edit = AddPlannedItemChildRelationshipEdit.create_unregistered(
            planned_item_parent,
            planned_item,
        )
        if not child_edit._is_valid:
            super(AddPlannedItemAsChildEdit, self).__init__([])
            self._is_valid = False
            return
        add_edit = AddPlannedItemEdit.create_unregistered(
            planned_item,
            index=index,
        )
        super(AddPlannedItemAsChildEdit, self).__init__([add_edit, child_edit])
        self._callback_args = self._undo_callback_args = [
            planned_item,
            planned_item.calendar_period,
            fallback_value(index, len(planned_item.get_item_container())),
        ]
        self._name = "AddPlannedItemAsChild ({0})".format(planned_item.name)
        self._description = (
            "Add {0} {1} and make it a child of {2} {3}".format(
                planned_item.__class__.__name__,
                planned_item.name,
                planned_item_parent.__class__.__name__,
                planned_item_parent.name,
            )
        )
