"""Callbacks to be used by tree manager class."""

from contextlib import contextmanager


class CallbackError(Exception):
    """Exception for callback class errors."""


class TreeCallbacks(object):
    """Class to store tree callbacks.

    This is intended to be used as a singleton through the TREE_CALLBACKS
    constant below and then accessed by tree manager classes. This means
    that though the ui will have multiple tree managers, they'll share the
    same callbacks.
    """
    def __init__(self):
        """Initialize."""
        self._pre_item_added_callbacks = {}
        self._item_added_callbacks = {}
        self._pre_item_removed_callbacks = {}
        self._item_removed_callbacks = {}
        self._pre_item_moved_callbacks = {}
        self._item_moved_callbacks = {}
        self._pre_item_modified_callbacks = {}
        self._item_modified_callbacks = {}

        self._all_callbacks = [
            self._pre_item_added_callbacks,
            self._item_added_callbacks,
            self._pre_item_removed_callbacks,
            self._item_removed_callbacks,
            self._pre_item_moved_callbacks,
            self._item_moved_callbacks,
            self._pre_item_modified_callbacks,
            self._item_modified_callbacks,
        ]

    ### Register Callbacks ###
    def register_pre_item_added_callback(self, id, callback):
        """Register pre item added callback.

        Args:
            id (variant): id to register callback at. Generally this will
                be the ui class that defines the callback.
            callback (function): callback to run before an item is added.
                This should accept arguments specified in the run func below.
        """
        if id in self._pre_item_added_callbacks:
            raise CallbackError(
                "there is already a pre_item_added_callback registered for "
                "{0}".format(str(id))
            )
        self._pre_item_added_callbacks[id] = callback

    def register_item_added_callback(self, id, callback):
        """Register item added callback.

        Args:
            id (variant): id to register callback at. Generally this will
                be the ui class that defines the callback.
            callback (function): callback to run when an item is added. This
                should accept arguments specified in the run func below.
        """
        if id in self._item_added_callbacks:
            raise CallbackError(
                "there is already an item_added_callback registered for "
                "{0}".format(str(id))
            )
        self._item_added_callbacks[id] = callback

    def register_pre_item_removed_callback(self, id, callback):
        """Register callback to use before an item is removed.

        Args:
            id (variant): id to register callback at. Generally this will
                be the ui class that defines the callback.
            callback (function): function to call before an item is removed.
                This should accept arguments specified in the run func below.
        """
        if id in self._pre_item_removed_callbacks:
            raise CallbackError(
                "there is already a pre_item_removed_callback registered for "
                "{0}".format(str(id))
            )
        self._pre_item_removed_callbacks[id] = callback

    def register_item_removed_callback(self, id, callback):
        """Register callback to use when an item is removed.

        Args:
            id (variant): id to register callback at. Generally this will
                be the ui class that defines the callback.
            callback (function): function to call when an item is removed.
                This should accept arguments specified in the run func below.
        """
        if id in self._item_removed_callbacks:
            raise CallbackError(
                "there is already an item_removed_callback registered for "
                "{0}".format(str(id))
            )
        self._item_removed_callbacks[id] = callback

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

    def register_pre_item_modified_callback(self, id, callback):
        """Register callback to use before an item is modified.

        Args:
            id (variant): id to register callback at. Generally this will
                be the ui class that defines the callback.
            callback (function): function to call before an item is modified.
                This should accept arguments specified in the run func below.
        """
        if id in self._pre_item_modified_callbacks:
            raise CallbackError(
                "there is already an _item_modified_callback registered for "
                "{0}".format(str(id))
            )
        self._item_modified_callbacks[id] = callback

    def register_item_modified_callback(self, id, callback):
        """Register callback to use when an item is modified.

        Args:
            id (variant): id to register callback at. Generally this will
                be the ui class that defines the callback.
            callback (function): function to call when an item is modified.
                This should accept arguments specified in the run func below.
        """
        if id in self._item_modified_callbacks:
            raise CallbackError(
                "there is already an _item_modified_callback registered for "
                "{0}".format(str(id))
            )
        self._item_modified_callbacks[id] = callback

    ### Run Callbacks ###
    def run_pre_item_added_callbacks(self, item, parent, index):
        """Run callbacks before an item has been added.

        Args:
            item (BaseTreeItem): the item that was added.
            parent (BaseTreeItem): the parent the item will be added under.
            index (int): the index the item will be added at.
        """
        for callback in self._pre_item_added_callbacks.values():
            callback(item, parent, index)

    def run_item_added_callbacks(self, item, parent, index):
        """Run callbacks after an item has been added.

        Args:
            item (BaseTreeItem): the item that was added.
            parent (BaseTreeItem): the parent the item will be added under.
            index (int): the index the item will be added at.
        """
        for callback in self._item_added_callbacks.values():
            callback(item, parent, index)

    def run_pre_item_removed_callbacks(self, item, parent, index):
        """Run callbacks before an item is removed.

        Args:
            item (BaseTreeItem): the item to remove.
            parent (BaseTreeItem): the parent the item will be added under.
            index (int): the index the item will be added at.
        """
        for callback in self._pre_item_removed_callbacks.values():
            callback(item, parent, index)

    def run_item_removed_callbacks(self, item, parent, index):
        """Run callbacks after an item has been removed.

        Args:
            item (BaseTreeItem): the removed item.
            parent (BaseTreeItem): the parent of the removed item.
            index (int): the old index of the removed item in its
                parent's child list.
        """
        for callback in self._item_removed_callbacks.values():
            callback(item, parent, index)

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
        for callback in self._pre_item_moved_callbacks.values():
            callback(item, old_parent, old_index, new_parent, new_index)
    
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
        for callback in self._item_moved_callbacks.values():
            callback(item, old_parent, old_index, new_parent, new_index)

    def run_pre_item_modified_callbacks(self, old_item, new_item):
        """Run callbacks before an item has been modified.

        Args:
            old_item (BaseTreeItem): the item pre-modification.
            new_item (BaseTreeItem): the item post-modification. This will
                usually be the same as old_item but may be different if the
                item has actually been replaced.
        """
        for callback in self._pre_item_modified_callbacks.values():
            callback(old_item, new_item)

    def run_item_modified_callbacks(self, old_item, new_item):
        """Run callbacks after an item has been modified.

        Args:
            old_item (BaseTreeItem): the item pre-modification.
            new_item (BaseTreeItem): the item post-modification. This will
                usually be the same as old_item but may be different if the
                item has actually been replaced.
        """
        for callback in self._item_modified_callbacks.values():
            callback(old_item, new_item)

    ### Remove Callbacks ##
    def remove_callbacks(self, id):
        """Remove all callbacks registered with given id.

        Args:
            id (variant): id to remove callbacks for.
        """
        for callback_dict in self._all_callbacks:
            if id in callback_dict:
                del callback_dict[id]


TREE_CALLBACKS = TreeCallbacks()
