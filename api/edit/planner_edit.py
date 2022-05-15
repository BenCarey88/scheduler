"""Planner edits to be applied to planned items.

Friend classes: [PlannedItem]
"""

from ._container_edit import ListEdit, ContainerOp, ContainerEditFlag
from ._core_edits import (
    AttributeEdit,
    CompositeEdit,
    SelfInverseSimpleEdit, 
    HostedDataEdit,
)


# TODO: calendar history edit - should just be extra part of
# UpdateTaskHistoryEdit class


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
            [(planned_item, index)],
            ContainerOp.INSERT,
        )
        self._name = "AddPlannedItem ({0})".format(planned_item.name)
        self._description = (
            "Add {0} {1} to {2} at index {3}".format(
                planned_item.__class__.__name__,
                planned_item.name,
                planned_item.date.string(),
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
            edit_flags=[ContainerEditFlag.REMOVE_BY_VALUE],
        )
        self._name = "RemovePlannedItem ({0})".format(planned_item.name)
        self._description = (
            "Remove {0} {1} at date {2}".format(
                planned_item.__class__.__name__,
                planned_item.name,
                planned_item.date.string(),
            )
        )


class MovePlannedItemEdit(ListEdit):
    """Move planned item in internal list."""
    def __init__(self, planned_item, index):
        """Initialise edit.

        Args:
            calendar_item (PlannedItem): the planned item to move.
            index (int): index to move to.
        """
        super(AddPlannedItemEdit, self).__init__(
            planned_item.get_item_container(),
            [(planned_item, index)],
            ContainerOp.MOVE,
        )
        self._name = "MovePlannedItem ({0})".format(planned_item.name)
        self._description = (
            "Move {0} {1} at date {2} to index {3}".format(
                planned_item.__class__.__name__,
                planned_item.name,
                planned_item.date.string(),
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
        subedits = attribute_edit
        if planned_item._date in attr_dict:
            new_date = attr_dict[planned_item._date]
            # remove items from old container and add to new one
            remove_edit = RemovePlannedItemEdit.create_unregistered(
                planned_item
            )
            add_edit = ListEdit.create_unregistered(
                planned_item.get_item_container(new_date),
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
