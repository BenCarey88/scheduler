"""Edit log to keep track of edits for undo/redo functionality."""


from contextlib import contextmanager


class EditUndefinedError(Exception):
    """Error for undo/redo called on an edit that's not fully defined."""
    def __init__(self, edit_name):
        super(EditUndefinedError, self).__init__(
            "Edit {0} has not been fully defined".format(edit_name)
        )


class UndoError(Exception):
    """Error for when undo is called on an edit that's already been undone."""
    def __init__(self, edit_name):
        super(UndoError, self).__init__(
            "Cannot undo edit {0}: already been undone.".format(edit_name)
        )


class RedoError(Exception):
    """Error for when redo is called on an edit that's not been undone."""
    def __init__(self, edit_name):
        super(UndoError, self).__init__(
            "Cannot redo edit {0}: has not been undone.".format(edit_name)
        )


class EditObject(object):
    """Class represeneting a single edit with undo, redo functionality."""

    def __init__(
            self,
            edit_function,
            edit_function_args=None,
            edit_function_kwargs=None):
        """Initialize edit object.

        Args:
            edit_function (function): the function that created the edit.
            edit_function_args (list): the function's args.
            edit_function_kwargs (dict): the function's kwargs.
        """
        self.redo_function = edit_function
        self.redo_function_args = edit_function_args or []
        self.redo_function_kwargs = edit_function_kwargs or {}
        self.undo_function = None
        self.undo_function_args = None
        self.undo_function_kwargs = None
        self.fully_defined = False
        self.undone = False

    def __repr__(self):
        """Get sring representation of self."""
        return "[EditObject {0}({1}, {2}); Undo {3}({4}, {5})]".format(
            str(self.redo_function),
            str(self.redo_function_args),
            str(self.redo_function_kwargs),
            str(self.undo_function),
            str(self.undo_function_args),
            str(self.undo_function_kwargs)
        )

    def set_undo_function(
            self,
            undo_function,
            undo_function_args=None,
            undo_function_kwargs=None):
        """Set the undo function for the edit object.

        Args:
            undo_function (function): function that can be used to undo the
                edit.
            undo_function_args (list): the function's args.
            undo_function_kwargs (dict): the function's kwargs.
        """
        self.undo_function = undo_function
        self.undo_function_args = undo_function_args or []
        self.undo_function_kwargs = undo_function_kwargs or {}
        self.fully_defined = True

    def undo(self):
        """Undo the edit by calling the undo function."""
        if not self.fully_defined:
            raise EditUndefinedError(self)
        if self.undone:
            raise UndoError(self)
        self.undo_function(
            *self.undo_function_args,
            **self.undo_function_kwargs
        )
        self.undone = True

    def redo(self):
        """Redo the edit by calling the redo function."""
        if not self.fully_defined:
            raise EditUndefinedError(self)
        if not self.undone:
            raise RedoError(self.name)
        self.redo_function(
            *self.redo_function_args,
            **self.redo_function_kwargs
        )
        self.undone = False


class EditLog(object):
    """Log of user edits made in tool."""

    def __init__(self):
        """Initialise edit log.

        Attributes:
            _log (list): list of past edits.
            _undo_log (list): list of edits that have previously been undone,
                saved so we can redo them.
            _registration_locked (bool): toggle to tell if the log is currently
                being modified. This allows us to not re-add functions to the
                log when they're being used to undo or redo.
            _current_edit (EditObject or None): the current_edit being added,
                if we're in the process of adding an edit.
        """
        self._log = []
        self._undo_log = []
        self._registration_locked = False
        self._current_edit = None

    @property
    def registration_locked(self):
        """Check if the registry is locked and hence no new edits can be added.

        The registry is locked if one of the following is occuring
        - the undo or redo functions are being called. This ensures that we
            don't add new edits while we're trying to undo/redo an old one.
        - we're in the process of adding an edit already, so self._current_edit
            is not None

        Returns:
            (bool): whether or not the registry is locked.
        """
        return self._registration_locked or not self._current_edit

    @contextmanager
    def lock_registry(self):
        """Context manager to lock registry while ."""
        self._registration_locked = True
        yield
        self._registration_locked = False

    @contextmanager
    def register_edit(self, edit):
        """Context manager to add a new edit to the log.

        This allows us to define the edit in two steps (defining the edit
        function first and then the undo function) and then only add the
        edit if both steps have been done.

        If the registration is locked, this does nothing.

        Args:
            edit (EditObject): the edit object to add. We assume that it is
                not fully defined when passed to the context manager but must
                be at the end in order to be added to the log.
        """
        can_register = self.registration_locked
        if can_register:
            self._current_edit = edit
        yield
        if can_register:
            if self._current_edit.fully_defined:
                self._add_edit(self._current_edit)
            self._current_edit = None

    def register_edit_inverse(self, function, args=None, kwargs=None):
        """Set undo function for the edit object currently being registered.

        Args:
            function (function): the function that created the edit.
            undo_function_args (list or None): the function's args.
            undo_function_kwargs (dict or None): the function's kwargs.
        """
        if self._current_edit:
            self._current_edit.set_undo_function(function, args, kwargs)

    def _add_edit(self, edit):
        """Add edit object to list.

        This will also clear the undo log, as we can no longer redo
        old undone edits once a new edit has been added.

        Args:
            edit (EditObject): edit object to add to list.
        """
        if self._undo_log:
            self._undo_log = []
        self.log.append(edit)

    def undo(self):
        """Undo most recent edit."""
        with self.lock_registry():
            try:
                edit = self._log.pop()
            except IndexError:
                return
            edit.undo()
            self._undo_log.append(edit)

    def redo(self):
        """Redo most recently undone edit."""
        with self.lock_registry():
            try:
                edit = self._undo_log.pop()
            except IndexError:
                return
            edit.redo()
            self._log.append(edit)


EDIT_LOG = EditLog()


def register_edit(function):
    """Decorator to register a function as an undoable/redoable edit.

    This requires that the function calls the register_edit_inverse
    function in order for the edit to actually be accepted and added
    to the edit log.

    add_to_edit_log=False is passed to the undo function to ensure it
    doesn't reregister the undo edit.
    """
    def decorated_function(*args, add_to_edit_log=True, **kwargs):
        if not add_to_edit_log or EDIT_LOG.registration_locked:
            return function(*args, **kwargs)
        edit = EditObject(function, args, kwargs)
        with EDIT_LOG.register_edit(edit):
            return function(*args, **kwargs)
    return decorated_function


def register_edit_inverse(function, args=None, kwargs=None):
    """Set the undo function for the edit object currently being registered.

    This needs to be added within a function that's being decorated with
    the regitster_edit decorator.

    Args:
        function (function): the function that created the edit.
        undo_function_args (list or None): the function's args.
        undo_function_kwargs (dict or None): the function's kwargs.
    """
    kwargs = kwargs or {}
    # add add_to_edit_log=False to kwargs so that the undo function isn't
    # re-registered
    kwargs["add_to_edit_log"] = False

    # in case undo function isn't registered, redefine function to ensure
    # it can accept the add_to_edit_log kwarg
    def modified_function(*_args, **_kwargs):
        try:
            return function(*_args, **_kwargs)
        except TypeError:
            del _kwargs["add_to_edit_log"]
            return function(*_args, **_kwargs)
    EDIT_LOG.register_edit_inverse(modified_function, args, kwargs)


def undo():
    """Run undo on edit log singleton."""
    EDIT_LOG.undo()


def redo():
    """Run redo on edit log singleton."""
    EDIT_LOG.redo()
