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
    def __init__(self, planned_item):
        """Initialise edit.

        Args:
            calendar_item (BaseCalendarItem): the calendar item to add. Can
                be a single calendar item instance or a repeating item.
        """

class RemovePlannedItemEdit(ListEdit):
    """"""

class ModifyPlannedItemAttributesEdit(CompositeEdit):
    """"""
