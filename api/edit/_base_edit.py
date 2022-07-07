"""Base edit class, containing edits that can be added to the edit log."""

from .edit_log import EDIT_LOG


class EditError(Exception):
    """General error class for all edit exceptions."""


class BaseEdit(object):
    """Base class representing an edit that we can register in the log.

    In general, subclasses need to implement _run and _inverse_run."""

    def __init__(self):
        """Initialise edit.

        Attributes:
            _register_edit (bool): whether or not to register this edit in the
                edit log (ie. whether or not it's a user edit that can be
                undone). By default this is true, but can be changed by
                creating the edit with the class method create_unregistered.
            _registered (bool): determines if the edit has been registered
                or not.
            _is_valid (bool): determines if edit is valid or not. This is used
                by the edit log to determine whether or not we should add the
                edit.
            _has_been_done (bool): used by undo/redo to determine if the
                edit has been done (and hence can be undone) or not (and
                hence can be run/redone).
            _callback_args (list or None): list of arguments to be used in
                edit callbacks, if callbacks accepted.
            _undo_callback_args (list or None): list of arguments to be used
                in undo edit callbacks, if callbacks accepted.
            _previous_edit_in_stack (BaseEdit or None): the previous edit in
                the edit stack, if this is part of one. An edit stack is a
                collection of edits that should all be undone/redone together.
            _next_edit_in_stack (BaseEdit or None): the previous edit in
                the edit stack, if this is part of one (see above for what an
                edit stack is). Note that both these attributes should not be
                modified by this class or its subclass, and are instead handled
                by the edit log.
            _name (str): name to use for edit in edit log.
            _description (str): description to use for edit in edit log.
            _edit_stack_name (str): name of any edit stack that contains this
                edit.
        """
        self._register_edit = True
        self._registered = False
        self._is_valid = True
        self._has_been_done = False
        self._callback_args = None
        self._undo_callback_args = None
        self._previous_edit_in_stack = None
        self._next_edit_in_stack = None
        self._name = "Unnamed Edit"
        self._description = ""
        self._edit_stack_name = (
            "This should be overridden in subclasses that support stacking."
        )

    @classmethod
    def create_and_run(cls, *args, **kwargs):
        """Create and run an edit.

        Args:
            args (tuple): args to pass to __init__.
            kwargs (dict): kwargs to pass to __init__.

        Returns:
            (bool): whether or not edit was successful (and hence added to
                the edit log).
        """
        edit = cls(*args, **kwargs)
        return edit.run()

    @classmethod
    def create_unregistered(cls, *args, **kwargs):
        """Create an unregistered edit. Used for subedits of composite edits.

        Args:
            args (tuple): args to pass to __init__.
            kwargs (dict): kwargs to pass to __init__.

        Returns:
            (BaseEdit): the edit object.
        """
        edit = cls(*args, **kwargs)
        edit._register_edit = False
        return edit

    @classmethod
    def register_pre_edit_callback(cls, id, callback):
        """Register callback to be run before an edit of this class is done.

        Args:
            id (variant): id for specific callback.
            callback (function): callback to register. Must accept this edit's
                _callback_args as arguments.
        """
        EDIT_LOG.register_pre_edit_callback(cls, id, callback)

    @classmethod
    def register_post_edit_callback(cls, id, callback):
        """Register callback to be run after an edit of this class is done.

        Args:
            id (variant): id for specific callback.
            callback (function): callback to register. Must accept this edit's
                _callback_args as arguments.
        """
        EDIT_LOG.register_post_edit_callback(cls, id, callback)

    @classmethod
    def register_pre_undo_callback(cls, id, callback):
        """Register callback to be run before an edit of this class is undone.

        Args:
            id (variant): id for specific callback.
            callback (function): callback to register. Must accept this edit's
                _undo_callback_args as arguments.
        """
        EDIT_LOG.register_pre_undo_callback(cls, id, callback)

    @classmethod
    def register_post_undo_callback(cls, id, callback):
        """Register callback to be run after an edit of this class is undone.

        Args:
            id (variant): id for specific callback.
            callback (function): callback to register. Must accept this edit's
                _undo_callback_args as arguments.
        """
        EDIT_LOG.register_post_undo_callback(cls, id, callback)

    def run(self):
        """Call edit function externally, and register with edit log if needed.

        This can only be called the once, if the edit is to be registered.
        When the EDIT_LOG wants to run the edit again for undoing/redoing, this
        is handled directly through the _run method.

        Returns:
            (bool): whether or not edit was successful (and hence added to
                the edit log).
        """
        if self._registered:
            raise EditError(
                "Edit object cannot be run externally after registration."
            )
        if self._has_been_done:
            raise EditError("Cannot run edit multiple times without undo.")
        if self._register_edit and EDIT_LOG.is_locked:
            # don't run registerable edits if they can't be added to log
            return False
        if self._is_valid:
            EDIT_LOG.run_pre_edit_callbacks(self)
            self._run()
            EDIT_LOG.run_post_edit_callbacks(self)
            if self._register_edit:
                self._registered = EDIT_LOG.add_edit(self)
        self._has_been_done = True
        return self._is_valid

    def _run(self):
        """Run edit function.

        If extra data is required for the implementation of _inverse_run (eg.
        the inverse_diff_dict in ContainerEdit), it is the responsibility
        of this function to ensure this data is defined.
        """
        raise NotImplementedError(
            "_run must be implemented in BaseEdit subclasses."
        )

    def _inverse_run(self):
        """Run inverse of edit function to undo edit.

        This should only be called after the _run function has been called, as
        it may be the case that some things required for the implementation of
        this method are defined in during _run (eg. inverse_diff_dict in
        ContainerEdit).
        """
        raise NotImplementedError(
            "_inverse_run must be reimplemented in BaseEdit subclasses."
        )

    def _undo(self):
        """Undo edit function."""
        if not self._has_been_done:
            raise EditError(
                "Can't call undo on edit that's already been undone."
            )
        EDIT_LOG.run_pre_undo_callbacks(self)
        self._inverse_run()
        EDIT_LOG.run_post_undo_callbacks(self)
        self._has_been_done = False

    def _redo(self):
        """Redo the edit function."""
        if self._has_been_done:
            raise EditError(
                "Can't call redo on edit that's not been undone."
            )
        EDIT_LOG.run_pre_edit_callbacks(self)
        self._run()
        EDIT_LOG.run_post_edit_callbacks(self)
        self._has_been_done = True

    def _stacks_with(self, edit):
        """Check if this should stack with edit if added to the log after it.

        This should be reimplemented in any subclasses that allow stacking.

        Args:
            edit (BaseEdit): edit to check if this should stack with.

        Returns:
            (bool): whether or not this should stack (by default this is
                always false).
        """
        return False

    @property
    def is_valid(self):
        """Check whether edit is valid (ie. actually changes underlying data).

        Returns:
            (bool): whether or not edit is valid.
        """
        return self._is_valid

    @property
    def name(self):
        """Get name of edit, to be displayed in edit log.
        
        Returns:
            (str): name of edit. This should be reimplemented in any subclasses
                that clients will actually call directly (or they can just
                redefine self._name).
        """
        return self._name

    @property
    def description(self):
        """Get description of edit to be used in edit log descriptions.

        Returns:
            (str): description of edit. This should be reimplemented in any
                subclasses that clients will actually call directly (or they
                can just redefine self._description).
        """
        return self._description

    @property
    def edit_stack_name(self):
        """Get name of edit stack, to be displayed in edit log.
        
        Returns:
            (str): name of an edit stack that contains this edit.
        """
        return self._edit_stack_name
