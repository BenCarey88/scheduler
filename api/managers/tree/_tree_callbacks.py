"""Callbacks to be used by tree manager class."""

from .. _base_callbacks import BaseCallbacks, CallbackError


class TreeCallbacks(BaseCallbacks):
    """Class to store tree callbacks.

    This is intended to be used as a singleton through the TREE_CALLBACKS
    constant below and then accessed by tree manager classes. This means
    that though the ui will have multiple tree managers, they'll share the
    same callbacks.
    """
    def __init__(self):
        """Initialize."""
        super(TreeCallbacks, self).__init__(include_move=True)

    def register_pre_item_moved_callback(self, id, callback):
        """Register callback to use before an item is moved.

        Args:
            id (variant): id to register callback at. Generally this will
                be the ui class that defines the callback.
            callback (function): function to call before an item is moved.
                This should accept arguments specified in the run func below.
        """
        if id in self._pre_item_moved_callbacks:
            raise CallbackError(
                "there is already a pre_item_moved_callback registered for "
                "{0}".format(str(id))
            )
        self._pre_item_moved_callbacks[id] = callback

    def register_item_moved_callback(self, id, callback):
        """Register callback to use when an item is moved.

        Args:
            id (variant): id to register callback at. Generally this will
                be the ui class that defines the callback.
            callback (function): function to call when an item is moved.
                This should accept arguments specified in the run func below.
        """
        if id in self._item_moved_callbacks:
            raise CallbackError(
                "there is already an item_moved_callback registered for "
                "{0}".format(str(id))
            )
        self._item_moved_callbacks[id] = callback

    ### Run Callbacks ###
    def run_pre_item_added_callbacks(self, item, parent, index):
        """Run callbacks before an item has been added.

        Args:
            item (BaseTreeItem): the item that was added.
            parent (BaseTreeItem): the parent the item will be added under.
            index (int): the index the item will be added at.
        """
        super(TreeCallbacks, self).run_pre_item_added_callbacks(
            item,
            parent,
            index,
        )

    def run_item_added_callbacks(self, item, parent, index):
        """Run callbacks after an item has been added.

        Args:
            item (BaseTreeItem): the item that was added.
            parent (BaseTreeItem): the parent the item will be added under.
            index (int): the index the item will be added at.
        """
        super(TreeCallbacks, self).run_item_added_callbacks(
            item,
            parent,
            index,
        )

    def run_pre_item_removed_callbacks(self, item, parent, index):
        """Run callbacks before an item is removed.

        Args:
            item (BaseTreeItem): the item to remove.
            parent (BaseTreeItem): the parent the item will be added under.
            index (int): the index the item will be added at.
        """
        super(TreeCallbacks, self).run_pre_item_removed_callbacks(
            item,
            parent,
            index,
        )

    def run_item_removed_callbacks(self, item, parent, index):
        """Run callbacks after an item has been removed.

        Args:
            item (BaseTreeItem): the removed item.
            parent (BaseTreeItem): the parent of the removed item.
            index (int): the old index of the removed item in its
                parent's child list.
        """
        super(TreeCallbacks, self).run_item_removed_callbacks(
            item,
            parent,
            index,
        )

    def run_pre_item_modified_callbacks(self, old_item, new_item):
        """Run callbacks before an item has been modified.

        Args:
            old_item (BaseTreeItem): the item pre-modification.
            new_item (BaseTreeItem): the item post-modification. This will
                usually be the same as old_item but may be different if the
                item has actually been replaced.
        """
        super(TreeCallbacks, self).run_pre_item_modified_callbacks(
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
        super(TreeCallbacks, self).run_pre_item_modified_callbacks(
            old_item,
            new_item,
        )

    def run_pre_item_moved_callbacks(
            self,
            item,
            old_parent,
            old_index,
            new_parent,
            new_index):
        """Run callbacks before an item is moved.

        Args:
            item (BaseTreeItem): the item to be moved.
            old_parent (BaseTreeItem): the original parent of the item.
            old_index (int): the original index of the item.
            new_parent (BaseTreeItem): the new parent of the moved item.
            new_index (int): the new index of the moved item.
        """
        super(TreeCallbacks, self).run_pre_item_moved_callbacks(
            item,
            old_parent,
            old_index,
            new_parent,
            new_index,
        )
    
    def run_item_moved_callbacks(
            self,
            item,
            old_parent,
            old_index,
            new_parent,
            new_index):
        """Run callbacks after an item has been moved.

        Args:
            item (BaseTreeItem): the item that was moved.
            old_parent (BaseTreeItem): the original parent of the item.
            old_index (int): the original index of the item.
            new_parent (BaseTreeItem): the new parent of the moved item.
            new_index (int): the new index of the moved item.
        """
        super(TreeCallbacks, self).run_item_moved_callbacks(
            item,
            old_parent,
            old_index,
            new_parent,
            new_index,
        )


TREE_CALLBACKS = TreeCallbacks()
