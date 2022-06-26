"""Callbacks to be used by planner manager class."""

from .._base_callbacks import BaseCallbacks, CallbackError


class PlannerCallbacks(BaseCallbacks):
    """Class to store planner callbacks.

    This is intended to be used as a singleton through the PLANNER_CALLBACKS
    constant below and then accessed by planner manager class.
    """
    def __init__(self):
        """Initialize."""
        super(PlannerCallbacks, self).__init__(
            include_move=True,
            include_full_update=True,
        )

    def run_pre_item_added_callbacks(self, item, index):
        """Run callbacks before an item has been added.

        Args:
            item (PlannedItem): the item to be added.
            index (int): index the item will be added at.
        """
        super(PlannerCallbacks, self).run_pre_item_added_callbacks(item, index)

    def run_item_added_callbacks(self, item, index):
        """Run callbacks after an item has been added.

        Args:
            item (PlannedItem): the item that was added.
            index (int): index the item was added at.
        """
        super(PlannerCallbacks, self).run_item_added_callbacks(item, index)

    def run_pre_item_removed_callbacks(self, item, index):
        """Run callbacks before an item is removed.

        Args:
            item (PlannedItem): the item to remove.
            index (int): index the item will be removed from.
        """
        super(PlannerCallbacks, self).run_pre_item_removed_callbacks(
            item,
            index,
        )

    def run_item_removed_callbacks(self, item, index):
        """Run callbacks after an item has been removed.

        Args:
            item (PlannedItem): the removed item.
            index (int): index the item was removed from.
        """
        super(PlannerCallbacks, self).run_item_removed_callbacks(item, index)

    def run_pre_item_modified_callbacks(self, old_item, new_item):
        """Run callbacks before an item has been modified.

        Args:
            old_item (PlannedItem): the item pre-modification.
            new_item (PlannedItem): the item post-modification. This will
                usually be the same as old_item but may be different if the
                item has actually been replaced.
        """
        super(PlannerCallbacks, self).run_pre_item_modified_callbacks(
            old_item,
            new_item,
        )

    def run_item_modified_callbacks(self, old_item, new_item):
        """Run callbacks after an item has been modified.

        Args:
            old_item (PlannedItem): the item pre-modification.
            new_item (PlannedItem): the item post-modification. This will
                usually be the same as old_item but may be different if the
                item has actually been replaced.
        """
        super(PlannerCallbacks, self).run_pre_item_modified_callbacks(
            old_item,
            new_item,
        )

    def run_pre_item_moved_callbacks(self, item, old_index, new_index):
        """Run callbacks before an item is moved.

        Args:
            item (PlannedItem): the item to move.
            old_index (int): previous index of item.
            new_index (int): new index of item.
        """
        super(PlannerCallbacks, self).run_pre_item_moved_callbacks(
            item,
            old_index,
            new_index,
        )

    def run_item_moved_callbacks(self, item, old_index, new_index):
        """Run callbacks after an item has been moved.

        Args:
            item (PlannedItem): the moved item.
            old_index (int): previous index of item.
            new_index (int): new index of item.
        """
        super(PlannerCallbacks, self).run_item_moved_callbacks(
            item,
            old_index,
            new_index,
        )

    def run_pre_full_update_callbacks(self):
        """Run callbacks before the data is updated."""
        super(PlannerCallbacks, self).run_pre_full_update_callbacks()

    def run_full_update_callbacks(self):
        """Run callbacks after the data has been updated."""
        super(PlannerCallbacks, self).run_full_update_callbacks()


PLANNER_CALLBACKS = PlannerCallbacks()
