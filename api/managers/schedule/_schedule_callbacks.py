"""Callbacks to be used by schedule manager class."""

from .. _base_callbacks import BaseCallbacks, CallbackError


class ScheduleCallbacks(BaseCallbacks):
    """Class to store scheduler callbacks.

    This is intended to be used as a singleton through the SCHEDULE_CALLBACKS
    constant below and then accessed by schedule manager class.
    """
    def run_pre_item_added_callbacks(self, item):
        """Run callbacks before an item has been added.

        Args:
            item (ScheduledItem): the item to be added.
        """
        super(ScheduleCallbacks, self).run_pre_item_added_callbacks(item)

    def run_item_added_callbacks(self, item):
        """Run callbacks after an item has been added.

        Args:
            item (ScheduledItem): the item that was added.
            parent (BaseTreeItem): the parent the item will be added under.
            index (int): the index the item will be added at.
        """
        super(ScheduleCallbacks, self).run_item_added_callbacks(item)

    def run_pre_item_removed_callbacks(self, item):
        """Run callbacks before an item is removed.

        Args:
            item (ScheduledItem): the item to remove.
        """
        super(ScheduleCallbacks, self).run_pre_item_removed_callbacks(item)

    def run_item_removed_callbacks(self, item):
        """Run callbacks after an item has been removed.

        Args:
            item (BaseTreeItem): the removed item.
            parent (BaseTreeItem): the parent of the removed item.
            index (int): the old index of the removed item in its
                parent's child list.
        """
        super(ScheduleCallbacks, self).run_item_removed_callbacks(item)

    def run_pre_item_modified_callbacks(self, old_item, new_item):
        """Run callbacks before an item has been modified.

        Args:
            old_item (BaseTreeItem): the item pre-modification.
            new_item (BaseTreeItem): the item post-modification. This will
                usually be the same as old_item but may be different if the
                item has actually been replaced.
        """
        super(ScheduleCallbacks, self).run_pre_item_modified_callbacks(
            old_item,
            new_item,
        )

    def run_item_modified_callbacks(self, old_item, new_item):
        """Run callbacks after an item has been modified.

        Args:
            old_item (BaseTreeItem): the item pre-modification.
            new_item (BaseTreeItem): the item post-modification. This will
                usually be the same as old_item but may be different if the
                item has actually been replaced.
        """
        super(ScheduleCallbacks, self).run_pre_item_modified_callbacks(
            old_item,
            new_item,
        )


SCHEDULE_CALLBACKS = ScheduleCallbacks()
