"""Edit log to keep track of edits for undo/redo functionality."""


from contextlib import contextmanager


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
        self._registration_locked = True
        self._current_edit = None

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
        yield
        self._registration_locked = _registration_locked

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


def open_edit_registry():
    """Unlock edit log singleton so edits can be registered."""
    EDIT_LOG.open_registry()


def undo():
    """Run undo on edit log singleton."""
    EDIT_LOG.undo()


def redo():
    """Run redo on edit log singleton."""
    EDIT_LOG.redo()
