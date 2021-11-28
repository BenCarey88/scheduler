"""Edit log to keep track of edits for undo/redo functionality."""


from contextlib import contextmanager


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
        """
        self._log = []
        self._undo_log = []
        self._registration_locked = True

    def get_current_edit_id(self):
        """Get id of most recent edit.

        Returns:
            (str): id of most recent edit.
        """
        if self._log:
            return self._log[-1].id

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
        self._unsaved_changes = True

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
            self._unsaved_changes = True
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
            self._unsaved_changes = True
            return True

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
        for edit in self._log:
            edit_string = edit.name
            if long:
                edit_string += "\n\t{0}".format(edit.description)
            edit_strings.append(edit_string)
        return "{0}{1}\n\n--------\n\n".format(
            title,
            "\n\n".join(edit_strings)
        )


# TODO: Now we have so many of these functions, is this still the best way to
# use the edit log singleton? In theory we could initialise it in the
# application, but remember that the singleton is also needed in the edit
# classes, so that may be a ball-ache - would still def need to be a singleton
# (because fuck passing the edit_log as an argument to each edit)
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


def current_edit_id():
    """Get id of most recent edit.

    Returns:
        (str): id of most recent edit.
    """
    return EDIT_LOG.get_current_edit_id()


def print_edit_log(long=True):
    """Print out edit log, for easy debugging.

    Args:
        long (bool): if True, we print the descriptions of each edit as well
            at their names.
    """
    print (EDIT_LOG.get_log_text(long=long))
