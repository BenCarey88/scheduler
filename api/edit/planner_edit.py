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
    """"""

class RemovePlannedItemEdit(ListEdit):
    """"""

class ModifyPlannedItemAttributesEdit(CompositeEdit):
    """"""
