"""Callbacks to be used by planner manager class."""

from scheduler.api.edit.planner_edit import (
    AddPlannedItemEdit,
    ModifyPlannedItemEdit,
    MovePlannedItemEdit,
    RemovePlannedItemEdit,
    SortPlannedItemsEdit,
)
from .. _base_callbacks import BaseCallbacks


class PlannerCallbacks(BaseCallbacks):
    """Class to store scheduler callbacks.

    This is intended to be used as a singleton through the SCHEDULE_CALLBACKS
    constant below and then accessed by schedule manager class.
    """
    def __init__(self):
        """Initialize.

        Callback args:
            add_edits: (planned_item)
            remove_edits: (planned_item)
            update_edits: (old_item, new_item)
            move_edits: (item, old_index, new_index)
            full_update: ()
        """
        super(PlannerCallbacks, self).__init__(
            add_item_edit_classes=(AddPlannedItemEdit,),
            remove_item_edit_classes=(RemovePlannedItemEdit,),
            update_item_edit_classes=(ModifyPlannedItemEdit,),
            move_item_edit_classes=(MovePlannedItemEdit,),
            full_update_edit_classes=(SortPlannedItemsEdit,),
        )


PLANNER_CALLBACKS = PlannerCallbacks()
