"""Edit log to keep track of edits for undo/redo functionality."""


from contextlib import contextmanager


class EditError(Exception):
    pass


class BaseEdit(object):
    """Base class representing an edit that we can register in the log."""

    def __init__(self, register_edit=True):
        """Initialise edit.
        
        Args:
            register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone).
        """
        self._register_edit = register_edit
        self._registered = False
        self._undone = True
        self._args = None
        self._kwargs = None
        self._inverse_edit = None

    @classmethod
    def from_inverse(cls, inverse_edit, *args, **kwargs):
        """Initiailise edit from inverse edit.

        Edits should always modify their args/kwargs, so the edit and
        its inverse should share the same args/kwargs.

        Args:
            inverse_edit (BaseEdit): inverse edit to initialise from.
            args (list): args to pass to __init__.
            kwargs (dict): kwargs to pass to __init__.]

        Returns:
            (BaseEdit): edit.
        """
        edit = cls(*args, **kwargs)
        edit._registered = True
        edit._args = inverse_edit._args
        edit._kwargs = inverse_edit._kwargs
        return edit

    def _run(self, *args, **kwargs):
        """Run edit and register with edit log if not already done so.

        Args:
            args (list): list of args this was called with.
            kwargs (dict): dict of kwargs this was called with.
        """
        if self._register_edit:
            if not self._registered:
                self._args = args
                self._kwargs = kwargs
                EDIT_LOG.add_edit(self)
                self._registered = True
            self._undone = False

    def _inverse(self):
        """Get inverse edit object.

        This needs to be run after the function is first called.

        Returns:
            (BaseEdit): Inverse BaseEdit, used to undo this one.
        """
        if self._inverse_edit:
            return self._inverse_edit
        if not self._registered:
            raise EditError(
                "_inverse must be called after edit has been run."
            )
        self._inverse_edit = self.from_inverse(self)
        return self._inverse_edit

    def __call__(self, *args, **kwargs):
        """Call edit function externally. This can only be done the once.

        This can only be done the once. Other calls are handled internally
        through the _run method and only used for undoing / redoing.

        Args:
            args (list): list of args this was called with.
            kwargs (dict): dict of kwargs this was called with.
        """
        if self._registered:
            raise EditError(
                "Edit object cannot be called externally after registration."
            )
        self._run(*args, **kwargs)

    def undo(self):
        """Undo edit function."""
        if self._undone:
            raise EditError(
                "Can't call undo on edit that's already been undone"
            )
        inverse_edit = self._inverse()
        inverse_edit._run(*inverse_edit._args, **inverse_edit._kwargs)
        self._undone = True

    def redo(self):
        """Redo the edit function."""
        if not self._undone:
            raise EditError(
                "Can't call redo on edit that's not been undone"
            )
        self._run(*self._args, **self._kwargs)
        self._undone = False


class EditLog(object):
    """Log of user edits made in tool."""

    def __init__(self):
        """Initialise edit log.

        Attributes:
            _log (list): list of past edits.
            _undo_log (list): list of edits that have previously been undone,
                saved so we can redo them.
            _registration_locked (bool): toggle to tell if the log is currently
                being modified. This allows us to ensure we don't re-add
                functions to the log when they're being used to undo or redo.
        """
        self._log = []
        self._undo_log = []
        self._registration_locked = False
        self._current_edit = None

    # SHOULDN'T BE NEEDED ANYMORE:
    @contextmanager
    def lock_registry(self):
        """Context manager to lock registry while ."""
        self._registration_locked = True
        yield
        self._registration_locked = False

    def add_edit(self, edit):
        """Add edit object to list.

        This will also clear the undo log, as we can no longer redo
        old undone edits once a new edit has been added.

        Args:
            edit (EditObject): edit object to add to list.
        """
        if self._registration_locked:
            return
        if self._undo_log:
            self._undo_log = []
        self._log.append(edit)

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
            edit.undo()
            self._undo_log.append(edit)
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
            edit.redo()
            self._log.append(edit)
            return True


EDIT_LOG = EditLog()


def undo():
    """Run undo on edit log singleton."""
    EDIT_LOG.undo()


def redo():
    """Run redo on edit log singleton."""
    EDIT_LOG.redo()
