"""Edit log to keep track of edits for undo/redo functionality."""


from contextlib import contextmanager


class CallbackError(Exception):
    """Exception for callback class errors."""


class EditLog(object):
    """Log of user edits made in tool.

    Friend Classes: [BaseEdit]
    """
    def __init__(self):
        """Initialise edit log.

        Attributes:
            _log (list): list of past edits.
            _undo_log (list): list of edits that have previously been undone,
                saved so we can redo them.
            _registration_locked (bool): toggle to tell if the log is currently
                being modified. This allows us to ensure we don't re-add
                functions to the log when they're being used to undo or redo.
            _pre_edit_callback_dict (dict): dictionary representing callbacks
                to be run before certain types of edit are done.
            _post_edit_callback_dict (dict): dictionary representing callbacks
                to be run before certain types of edit are done.
            _pre_undo_callback_dict (dict): dictionary representing callbacks
                to be run before certain types of edit are undone.
            _post_undo_callback_dict (dict): dictionary representing callbacks
                to be run after certain types of edit are undone.
        """
        self._log = []
        self._undo_log = []
        self._registration_locked = True
        self._pre_edit_callback_dict = {}
        self._post_edit_callback_dict = {}
        self._pre_undo_callback_dict = {}
        self._post_undo_callback_dict = {}

    @property
    def is_locked(self):
        """Check whether edit log is locked.

        Returns:
            (bool): whether or not edit log registration is locked.
        """
        return self._registration_locked

    def register_pre_edit_callback(self, edit_class, callback_id, callback):
        """Register callback to be run before an an edit of given type is done.

        Args:
            edit_class (class): edit class we're registering callback for..
            callback_id (variant): id for specific callback.
            callback (function): callback to register.
        """
        callbacks_dict = self._pre_edit_callback_dict.setdefault(edit_class, {})
        if callback_id in callbacks_dict:
            raise CallbackError(
                "There is already a pre_edit_callback with id {0} registered "
                "for edit class {1}".format(str(callback_id), edit_class)
            )
        callbacks_dict[callback_id] = callback

    def register_post_edit_callback(self, edit_class, callback_id, callback):
        """Register callback to be run after an an edit of given type is done.

        Args:
            edit_class (class): edit class we're registering callback for..
            callback_id (variant): id for specific callback.
            callback (function): callback to register.
        """
        callbacks_dict = self._post_edit_callback_dict.setdefault(edit_class, {})
        if callback_id in callbacks_dict:
            raise CallbackError(
                "There is already a post_edit_callback with id {0} registered "
                "for edit class {1}".format(str(callback_id), edit_class)
            )
        callbacks_dict[callback_id] = callback

    def register_pre_undo_callback(self, edit_class, callback_id, callback):
        """Register callback to be run before an edit of given type is undone.

        Args:
            edit_class (class): edit class we're registering callback for..
            callback_id (variant): id for specific callback.
            callback (function): callback to register.
        """
        callbacks_dict = self._pre_undo_callback_dict.setdefault(edit_class, {})
        if callback_id in callbacks_dict:
            raise CallbackError(
                "There is already a pre_undo_callback with id {0} registered "
                "for edit class {1}".format(str(callback_id), edit_class)
            )
        callbacks_dict[callback_id] = callback

    def register_post_undo_callback(self, edit_class, callback_id, callback):
        """Register callback to be run after an edit of given type is undone.

        Args:
            edit_class (class): edit class we're registering callback for.
            callback_id (variant): id for specific callback.
            callback (function): callback to register.
        """
        callbacks_dict = self._post_undo_callback_dict.setdefault(edit_class, {})
        if callback_id in callbacks_dict:
            raise CallbackError(
                "There is already a post_undo_callback with id {0} registered "
                "for edit class {1}".format(str(callback_id), edit_class)
            )
        callbacks_dict[callback_id] = callback

    def run_pre_edit_callbacks(self, edit):
        """Run callbacks before a given edit is done.

        Args:
            edit (BaseEdit): the edit to run for.
        """
        callbacks = self._pre_edit_callback_dict.get(type(edit), {})
        for callback in callbacks.values():
            callback(*edit._callback_args)

    def run_post_edit_callbacks(self, edit):
        """Run callbacks after a given edit is done.

        Args:
            edit (BaseEdit): the edit to run for.
        """
        callbacks = self._post_edit_callback_dict.get(type(edit), {})
        for callback in callbacks.values():
            callback(*edit._callback_args)

    def run_pre_undo_callbacks(self, edit):
        """Run callbacks before a given edit is undone.

        Args:
            edit (BaseEdit): the edit to run for.
        """
        callbacks = self._pre_undo_callback_dict.get(type(edit), {})
        for callback in callbacks.values():
            callback(*edit._undo_callback_args)

    def run_post_undo_callbacks(self, edit):
        """Run callbacks after a given edit is undone.

        Args:
            edit (BaseEdit): the edit to run for.
        """
        callbacks = self._post_undo_callback_dict.get(type(edit), {})
        for callback in callbacks.values():
            callback(*edit._undo_callback_args)

    def remove_callbacks(self, callback_id):
        """Remove all callbacks with the given callback id from the registry.

        Args:
            callback_id (variant): id for callback.
        """
        callback_dicts = (
            self._pre_edit_callback_dict,
            self._post_edit_callback_dict,
            self._pre_undo_callback_dict,
            self._post_undo_callback_dict,
        )
        for callback_dict in callback_dicts:
            for callback_subdict in callback_dict.values():
                if callback_id in callback_subdict:
                    del callback_subdict[callback_id]

    def open_registry(self):
        """Open edit registry so edits can be added."""
        self._registration_locked = False

    @contextmanager
    def lock_registry(self):
        """Context manager to lock registry while undoing/redoing.

        In theory this shouldn't be needed right now but maybe could be
        useful/necessary down the line.
        """
        _registration_locked = self._registration_locked
        self._registration_locked = True
        try:
            yield
        finally:
            self._registration_locked = _registration_locked

    def add_edit(self, edit):
        """Add edit object to list.

        This will also clear the undo log, as we can no longer redo
        old undone edits once a new edit has been added.

        Args:
            edit (BaseEdit): edit object to add to list.

        Returns:
            (bool): whether or not edit was successfully added.
        """
        if self._registration_locked:
            return False
        if not edit._is_valid:
            return False
        if self._undo_log:
            self._undo_log = []
        latest_edit = self.get_latest_edit()
        if latest_edit is not None and edit._stacks_with(latest_edit):
            edit._previous_edit_in_stack = latest_edit
            latest_edit._next_edit_in_stack = edit
        self._log.append(edit)
        return True

    def undo(self):
        """Undo most recent edit.

        Returns:
            (bool): whether or not undo was successful.
        """
        with self.lock_registry():
            try:
                edit = self._log.pop()
            except IndexError:
                return False
            edit._undo()
            self._undo_log.append(edit)
        if edit._previous_edit_in_stack is not None:
            self.undo()
        return True

    def redo(self):
        """Redo most recently undone edit.

        Returns:
            (bool): whether or not redo was successful.
        """
        with self.lock_registry():
            try:
                edit = self._undo_log.pop()
            except IndexError:
                return False
            edit._redo()
            self._log.append(edit)
        if edit._next_edit_in_stack is not None:
            self.redo()
        return True

    def get_latest_edit(self):
        """Get most recent edit.

        Returns:
            (BaseEdit or None): most recent edit, if one exists.
        """
        if self._log:
            return self._log[-1]
        return None

    def get_log_text(self, long=True):
        """Get string representation of all edits in edit log.

        Args:
            long (bool): if True, we get the descriptions of each edit as well
                at their names.

        Returns:
            (str): edit log text.
        """
        edit_strings = []
        title = "\n--------\nEDIT LOG\n--------\n\n"
        if not self._log:
            return "{0}[EMPTY]\n\n".format(title)

        edit_stack_string = None
        for edit in self._log:
            # if edit is part of stack, use edit_stack_name (and descriptions)
            if edit._next_edit_in_stack is not None:
                if edit_stack_string is None:
                    edit_stack_string = edit.edit_stack_name
                if long:
                    edit_stack_string += "\n\t{0}".format(edit.description)
            # if this is the last item of an edit stack, add to edit_strings
            elif edit_stack_string is not None:
                if long:
                    edit_stack_string += "\n\t{0}".format(edit.description)
                edit_strings.append(edit_stack_string)
                edit_stack_string = None
            # if no stack, just use the edit name (and descriptions)
            else:
                edit_string = edit.name
                if long:
                    edit_string += "\n\t{0}".format(edit.description)
                edit_strings.append(edit_string)

        return "{0}{1}\n\n--------\n\n".format(
            title,
            "\n\n".join(edit_strings)
        )


EDIT_LOG = EditLog()


def open_edit_registry():
    """Unlock edit log singleton so edits can be registered."""
    EDIT_LOG.open_registry()


def undo():
    """Run undo on edit log singleton.

    Returns:
        (bool): whether or not undo was performed.
    """
    return EDIT_LOG.undo()


def redo():
    """Run redo on edit log singleton.

    Returns:
        (bool): whether or not redo was performed.
    """
    return EDIT_LOG.redo()


def latest_edit():
    """Get most recent edit.

    Returns:
        (BaseEdit or None): most recent edit, if one exists.
    """
    return EDIT_LOG.get_latest_edit()


def remove_edit_callbacks(callback_id):
    """Remove all callbacks with the given callback id.

    Args:
        callback_id (variant): id to remove. This usually represents the
            ui class that defines the given callbacks.
    """
    EDIT_LOG.remove_callbacks(callback_id)


def print_edit_log(long=True):
    """Print out edit log, for easy debugging.

    Args:
        long (bool): if True, we print the descriptions of each edit as well
            at their names.
    """
    print (EDIT_LOG.get_log_text(long=long))
