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
            _edit_to_add (BaseEdit or None): edit that we're in the process
                of performing and adding to the log. This is used for
                continuous edits where the edit can be updated continuously by
                the user before being added to the log (eg. dragging a calendar
                item to change its time).
        """
        self._log = []
        self._undo_log = []
        self.__registration_locked = True
        self._edit_to_add = None

    @property
    def _registration_locked(self):
        """Check whether registration is locked.

        We treat the edit registry as locked if either:
            - the __registration_locked attribute is True
            - there is an edit currently saved in the _edit_to_add attribute

        Returns:
            (bool): whether or not edit registration is locked.
        """
        return (self.__registration_locked or self._edit_to_add is not None)

    @property
    def is_locked(self):
        """Check whether edit log is locked.

        Returns:
            (bool): whether or not edit log registration is locked.
        """
        return self._registration_locked

    def open_registry(self):
        """Open edit registry so edits can be added."""
        self.__registration_locked = False

    @contextmanager
    def lock_registry(self):
        """Context manager to lock registry while undoing/redoing.

        In theory this shouldn't be needed right now but maybe could be
        useful/necessary down the line.
        """
        __registration_locked = self.__registration_locked
        self.__registration_locked = True
        try:
            yield
        finally:
            self.__registration_locked = __registration_locked

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
        self._log.append(edit)
        return True

    def begin_add_edit(self, edit):
        """Begin adding edit to log.

        This is for continuous edits, where the edit can be updated
        continuously by the user before being added to the log (eg. dragging
        a calendar item to change its time).

        Args:
            edit (BaseEdit): edit object to register.
        """
        self._edit_to_add = edit

    def end_add_edit(self):
        """Finish adding edit to log and unlock registry."""
        edit = self._edit_to_add
        self._edit_to_add = None
        self.add_edit(edit)

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


def latest_edit():
    """Get most recent edit.

    Returns:
        (BaseEdit or None): most recent edit, if one exists.
    """
    return EDIT_LOG.get_latest_edit()


def print_edit_log(long=True):
    """Print out edit log, for easy debugging.

    Args:
        long (bool): if True, we print the descriptions of each edit as well
            at their names.
    """
    print (EDIT_LOG.get_log_text(long=long))
