"""Callbacks to be used by manager classes after edits."""


class CallbackError(Exception):
    """Exception for callback class errors."""


class BaseCallbacks(object):
    """Class to store callbacks."""
    def __init__(self, include_move=False, include_full_update=False):
        """Initialize.

        Args:
            include_move (bool): if True, include move callbacks too.
            include_complete_update (bool): if True, include callbacks that
                represent a complete update to the whole model.
        """
        self._pre_item_added_callbacks = {}
        self._item_added_callbacks = {}
        self._pre_item_removed_callbacks = {}
        self._item_removed_callbacks = {}
        self._pre_item_modified_callbacks = {}
        self._item_modified_callbacks = {}
        if include_move:
            self._pre_item_moved_callbacks = {}
            self._item_moved_callbacks = {}
        if include_full_update:
            self._pre_full_update_callbacks = {}
            self._full_update_callbacks = {}

        self._all_callbacks = [
            self._pre_item_added_callbacks,
            self._item_added_callbacks,
            self._pre_item_removed_callbacks,
            self._item_removed_callbacks,
            self._pre_item_modified_callbacks,
            self._item_modified_callbacks,
        ]
        if include_move:
            self._all_callbacks.extend([
                self._pre_item_moved_callbacks,
                self._item_moved_callbacks,
            ])
        if include_full_update:
            self._all_callbacks.extend([
                self._pre_full_update_callbacks,
                self._full_update_callbacks,
            ])

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

    def register_pre_full_update_callback(self, id, callback):
        """Register callback to use before the underlying data is updated.

        Args:
            id (variant): id to register callback at. Generally this will
                be the ui class that defines the callback.
            callback (function): function to call before the update.
        """
        if id in self._pre_full_update_callbacks:
            raise CallbackError(
                "there is already an _pre_full_update_callback registered for "
                "{0}".format(str(id))
            )
        self._pre_full_update_callbacks[id] = callback

    def register_full_update_callback(self, id, callback):
        """Register callback to use when the underlying data is updated.

        Args:
            id (variant): id to register callback at. Generally this will
                be the ui class that defines the callback.
            callback (function): function to call before the update.
        """
        if id in self._full_update_callbacks:
            raise CallbackError(
                "there is already an _full_update_callback registered for "
                "{0}".format(str(id))
            )
        self._full_update_callbacks[id] = callback

    ### Run Callbacks ###
    def run_pre_item_added_callbacks(self, *args, **kwargs):
        """Run callbacks before an item has been added.

        Args should be defined in subclasses.
        """
        for callback in self._pre_item_added_callbacks.values():
            callback(*args, **kwargs)

    def run_item_added_callbacks(self, *args, **kwargs):
        """Run callbacks after an item has been added.

        Args should be defined in subclasses.
        """
        for callback in self._item_added_callbacks.values():
            callback(*args, **kwargs)

    def run_pre_item_removed_callbacks(self, *args, **kwargs):
        """Run callbacks before an item is removed.

        Args should be defined in subclasses.
        """
        for callback in self._pre_item_removed_callbacks.values():
            callback(*args, **kwargs)

    def run_item_removed_callbacks(self, *args, **kwargs):
        """Run callbacks after an item has been removed.

        Args should be defined in subclasses.
        """
        for callback in self._item_removed_callbacks.values():
            callback(*args, **kwargs)

    def run_pre_item_modified_callbacks(self, *args, **kwargs):
        """Run callbacks before an item has been modified.

        Args should be defined in subclasses.
        """
        for callback in self._pre_item_modified_callbacks.values():
            callback(*args, **kwargs)

    def run_item_modified_callbacks(self, *args, **kwargs):
        """Run callbacks after an item has been modified.

        Args should be defined in subclasses.
        """
        for callback in self._item_modified_callbacks.values():
            callback(*args, **kwargs)

    def run_pre_item_moved_callbacks(self, *args, **kwargs):
        """Run callbacks before an item is moved.

        Args should be defined in subclasses.
        """
        for callback in self._pre_item_moved_callbacks.values():
            callback(*args, **kwargs)

    def run_item_moved_callbacks(self, *args, **kwargs):
        """Run callbacks after an item has been moved.

        Args should be defined in subclasses.
        """
        for callback in self._item_moved_callbacks.values():
            callback(*args, **kwargs)

    def run_pre_full_update_callbacks(self, *args, **kwargs):
        """Run callbacks before the data is updated.

        Args should be defined in subclasses.
        """
        for callback in self._pre_full_update_callbacks.values():
            callback(*args, **kwargs)

    def run_full_update_callbacks(self, *args, **kwargs):
        """Run callbacks after the data has been updated.

        Args should be defined in subclasses.
        """
        for callback in self._full_update_callbacks.values():
            callback(*args, **kwargs)

    ### Remove Callbacks ##
    def remove_callbacks(self, id):
        """Remove all callbacks registered with given id.

        Args:
            id (variant): id to remove callbacks for.
        """
        for callback_dict in self._all_callbacks:
            if id in callback_dict:
                del callback_dict[id]
