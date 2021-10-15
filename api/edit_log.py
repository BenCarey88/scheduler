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


class EditLog(object):
    """Log of user edits made in tool."""

    def __init__(self):
        """Initialise edit log.

        Attributes:
            log (list): list of past edits.
            redo_log (list): list of edits that have previously been undone,
                saved so we can redo them.
            update_in_progress (bool): toggle to tell if the log is currently
                being modified. This allows us to not re-add functions to the
                log when they're being used to undo or redo.
        """
        self.log = []
        self.redo_log = []
        self.update_in_progress = False

    @contextmanager
    def lock_other_edits(self):
        """Context manager to stop the further updates while one is being done."""
        self.update_in_progress = True
        yield
        self.update_in_progress = False

    def add_edit(self, edit):
        """Add edit object to list.

        If current index of edit list is not at end of list, this means the
        user has undone up to that point, so adding the edit will remove all
        edits beyond the current index from the list.

        Args:
            edit (EditObject): edit object to add to list.
        """
        if self.update_in_progress:
            return
        if not edit.fully_defined:
            raise EditUndefinedError(edit)
        if self.redo_log:
            self.redo_log = []
        self.log.append(edit)

    def undo(self):
        """Undo most recent edit."""
        if self.update_in_progress:
            return
        with self.lock_other_edits():
            try:
                edit = self.log.pop()
            except IndexError:
                return
            edit.undo()
            self.redo_log.append(edit)

    def redo(self):
        """Redo most recently undone edit."""
        if self.update_in_progress:
            return
        with self.lock_other_edits():
            try:
                edit = self.redo_log.pop()
            except IndexError:
                return
            edit.redo()
            self.log.append(edit)


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
        return "[EditObject {0}({1}, {2})]".format(
            str(self.redo_function),
            str(self.redo_function_args),
            str(self.redo_function_kwargs)
        )

    def set_undo_function(
            self,
            undo_function,
            undo_function_args=None,
            undo_function_kwargs=None):
        """Set the undo function for the edit object.

        Args:
            undo_function (function): the function that created the edit.
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


EDIT_LOG = EditLog()


def register_edit(function):
    """Decorator to register a function as an undoable/redoable edit.

    This requires passing the 'edit_object' as an argument to the function
    that's to be decorated, and setting the undo function on the edit
    object as part of the function definition.

    It also allows passing the boolean argument 'add_to_edit_log' to give
    the control over whether a particular call of the decorated function
    will be treated as an undoable/redoable edit.
    """
    def decorated_function(*args, **kwargs):
        edit = EditObject(function, args, kwargs)
        with EDIT_LOG.lock_other_edits():
            function(*args, **kwargs, edit_object=edit)
        if kwargs.get("add_to_edit_log", True):
            EDIT_LOG.add_edit(edit)
    return decorated_function


def undo():
    """Run undo on edit log singleton."""
    EDIT_LOG.undo()


def redo():
    """Run redo on edit log singleton."""
    EDIT_LOG.redo()
